/**
 * api.js — HTTP client with JWT bearer token support.
 * Configuration is read from config.js — import from there directly,
 * not via this module.
 *
 * 401 interceptor: any 401 response clears the stored token and
 * triggers a full session reset so the user is returned to the login
 * screen automatically.
 */
import { API_BASE_URL } from '../config.js';

const TOKEN_KEY = 'sc_auth_token';
export const setToken = t => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
export const getToken = ()  => localStorage.getItem(TOKEN_KEY);

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

/**
 * @param {string} path
 * @param {string} method
 * @param {any} [body]
 * @param {{ skip401Logout?: boolean }} [opts]
 *   skip401Logout — do not treat a 401 from this call as "the session died".
 *   Needed for endpoints where 401 means something else: PATCH /user/password
 *   returns it when the *supplied* old password is wrong, and signing the
 *   user out because they made a typo would be absurd.
 */
async function request(path, method, body, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token   = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method, headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = null;
  if ((res.headers.get('content-type') || '').includes('application/json'))
    data = await res.json();
  if (!res.ok) {
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
