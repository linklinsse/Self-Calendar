/**
 * auth.service.js — Authentication via OAuth2 password flow.
 *
 * Login:  POST /token   (form-encoded)  → { access_token, token_type }
 * Me:     GET  /user/me                 → ObjUserSchemaComplete
 * Logout: client-side only (clear token)
 *
 * Note: The API exposes GET /auth/login which likely initiates an OAuth
 * redirect. For username/password flow we POST to the tokenUrl "token"
 * as declared in the OpenAPI securitySchemes.
 */

import { MOCK_MODE } from '../config.js';
import { api, setToken, getToken } from './api.js';
import { MOCK_USER } from '../sampleData.js';

/** @typedef {{ id:string, login:string }} User */

/**
 * Login with username + password (OAuth2 password grant).
 * @param {string} username
 * @param {string} password
 * @returns {Promise<User>}
 */
export async function login(username, password) {
  if (MOCK_MODE) {
    await new Promise(r => setTimeout(r, 400));
    setToken('mock-token');
    return MOCK_USER;
  }

  const res = await api.post(`/auth/login`, { username, password })

  setToken(res);
  return getMe();
}

/**
 * Register a new account.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<User>}
 */
export async function register(username, password) {
  if (MOCK_MODE) {
    await new Promise(r => setTimeout(r, 500));
    setToken('mock-token');
    return { ...MOCK_USER, login: username };
  }
  await api.post('/auth/register', { username, password });
  // Auto-login after registration
  return login(username, password);
}

/**
 * Log out — clears local token only (no server-side logout endpoint).
 * @returns {Promise<void>}
 */
export async function logout() {
  setToken(null);
}

/**
 * Fetch the currently authenticated user from GET /user/me.
 * @returns {Promise<User|null>}
 */
export async function getMe() {
  if (MOCK_MODE) return getToken() ? MOCK_USER : null;
  try {
    const u = await api.get('/auth/me');
    // Normalise: API returns { id, login, hashed_password } — expose as { id, login, name }
    return { ...u, name: u.login };
  } catch {
    return null;
  }
}
