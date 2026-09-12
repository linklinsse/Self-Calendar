/**
 * api.js — HTTP client with JWT bearer token support.
 * Configuration is read from config.js — import from there directly,
 * not via this module.
 *
 * 401 interceptor: a 401 first tries a silent refresh (see attemptRefresh)
 * using the stored refresh token — the access token is only 24h, and
 * without this the user was bounced to the login screen daily. Only when
 * that also fails does it clear the stored token and trigger a full
 * session reset so the user is returned to the login screen.
 */
import { API_BASE_URL } from '../config.js';

const TOKEN_KEY = 'sc_auth_token';
export const setToken = t => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
export const getToken = ()  => localStorage.getItem(TOKEN_KEY);

const REFRESH_TOKEN_KEY = 'sc_refresh_token';
export const setRefreshToken = t => t ? localStorage.setItem(REFRESH_TOKEN_KEY, t) : localStorage.removeItem(REFRESH_TOKEN_KEY);
export const getRefreshToken = ()  => localStorage.getItem(REFRESH_TOKEN_KEY);

export class ApiError extends Error {
  constructor(status, message, body = null) {
    super(message); this.name = 'ApiError'; this.status = status; this.body = body;
    /**
     * The API's own error_code (see api/app/common/errors.py), lifted out of
     * the envelope so callers can branch on the specific failure instead of
     * pattern-matching the human-readable message.
     * @type {string|null}
     */
    this.code = body?.detail?.error_code ?? null;
  }
}

// ── 401 interceptor ───────────────────────────────────────────
// Imported lazily (inside the function) to avoid a circular
// dependency: api ← auth.service ← stores/index ← api.
function handle401() {
  setToken(null);
  // Dynamically import the store reset so this module stays
  // free of circular deps at module-evaluation time.
  import('../stores/index.js').then(({ logoutUser }) => logoutUser()).catch(() => {
    // Last resort: hard reload if the store import itself fails.
    window.location.reload();
  });
}

// Paths where a 401 retried-via-refresh would be meaningless: /auth/login
// and /auth/register 401 because the *credentials* are wrong, not because a
// session expired, and /auth/refresh is the refresh call itself (already
// guarded with skip401Logout below, but excluded here too for clarity).
const NO_REFRESH_RETRY_PATHS = new Set(['/auth/login', '/auth/register', '/auth/refresh']);

// Dedupes concurrent refresh attempts: the app fires several requests in
// parallel on boot (calendars, categories, ...), and without this an
// expired token would trigger one /auth/refresh call per request instead
// of one shared one.
let _refreshInFlight = null;

/** Exchange the stored refresh token for a fresh access token. Returns
 * whether it succeeded; on failure the (presumably dead) refresh token is
 * dropped so future 401s don't keep retrying it. */
function attemptRefresh() {
  if (_refreshInFlight) return _refreshInFlight;

  const refreshToken = getRefreshToken();
  if (!refreshToken) return Promise.resolve(false);

  _refreshInFlight = (async () => {
    try {
      const newToken = await request(
        '/auth/refresh', 'POST', { refresh_token: refreshToken }, { skip401Logout: true }
      );
      if (!newToken) return false;
      setToken(newToken);
      return true;
    } catch {
      setRefreshToken(null);
      return false;
    }
  })();

  return _refreshInFlight.finally(() => { _refreshInFlight = null; });
}

/**
 * @param {string} path
 * @param {string} method
 * @param {any} [body]
 * @param {{ skip401Logout?: boolean }} [opts]
 *   skip401Logout — do not treat a 401 from this call as "the session died".
 *   Needed for endpoints where 401 means something else: PATCH /user/password
 *   returns it when the *supplied* old password is wrong, and signing the
 *   user out because they made a typo would be absurd.
 * @param {boolean} [_retried] — internal: set once a refresh-and-retry has
 *   already happened for this call, so a second 401 goes straight to logout
 *   instead of looping.
 */
async function request(path, method, body, opts = {}, _retried = false) {
  const headers = { 'Content-Type': 'application/json' };
  const token   = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method, headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = null;
  // 204 (e.g. DELETE /category/{id}) carries no body but can still set a
  // JSON content-type header, and res.json() throws SyntaxError on an
  // empty string — reading as text first and parsing only if non-empty
  // avoids the empty-body case regardless of what the header says.
  if (res.status !== 204 && (res.headers.get('content-type') || '').includes('application/json')) {
    const text = await res.text();
    data = text ? JSON.parse(text) : null;
  }
  if (!res.ok) {
    if (res.status === 401 && !opts.skip401Logout && !_retried && !NO_REFRESH_RETRY_PATHS.has(path)) {
      if (await attemptRefresh()) return request(path, method, body, opts, true);
    }
    if (res.status === 401 && !opts.skip401Logout) handle401();
    throw new ApiError(res.status, data?.detail?.message || data?.detail || data?.message || res.statusText, data);
  }
  return data;
}

export const api = {
  get:    (path, o)     => request(path, 'GET',    undefined, o),
  post:   (path, b, o)  => request(path, 'POST',   b, o),
  put:    (path, b, o)  => request(path, 'PUT',    b, o),
  patch:  (path, b, o)  => request(path, 'PATCH',  b, o),
  delete: (path, o)     => request(path, 'DELETE', undefined, o),
};
