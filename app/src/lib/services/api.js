/**
 * api.js — HTTP client with JWT bearer token support.
 * Configuration is read from config.js — import from there directly,
 * not via this module.
 *
 * 401 interceptor: any 401 response clears the stored token and
 * triggers a full session reset so the user is returned to the login
 * screen automatically.
 */
import { API_BASE_URL, MOCK_MODE } from '../config.js';

const TOKEN_KEY = 'sc_auth_token';
export const setToken = t => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
export const getToken = ()  => localStorage.getItem(TOKEN_KEY);

export class ApiError extends Error {
  constructor(status, message, body = null) {
    super(message); this.name = 'ApiError'; this.status = status; this.body = body;
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

async function request(path, method, body) {
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
    if (res.status === 401) handle401();
    throw new ApiError(res.status, data?.message || data?.error || res.statusText, data);
  }
  return data;
}

export const api = {
  get:    path       => MOCK_MODE ? Promise.resolve(null) : request(path, 'GET'),
  post:   (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'POST',   b),
  put:    (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'PUT',    b),
  patch:  (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'PATCH',  b),
  delete: path       => MOCK_MODE ? Promise.resolve(null) : request(path, 'DELETE'),
};
