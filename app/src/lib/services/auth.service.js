/**
 * auth.service.js — Authentication.
 *
 * Login:    POST /auth/login    (JSON body: username/password) → raw JWT string
 * Register: POST /auth/register (JSON body: username/password) → user object, then auto-login
 * Me:       GET  /auth/me                                      → { id, username }
 * Logout:   client-side only (clear token)
 */

import { api, setToken } from './api.js';

/** @typedef {{ id:string, login:string }} User */

/**
 * Login with username + password (OAuth2 password grant).
 * @param {string} username
 * @param {string} password
 * @returns {Promise<User>}
 */
export async function login(username, password) {
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
  try {
    const u = await api.get('/auth/me');
    // Normalise: API returns { id, username } — expose as { id, username, name }
    return { ...u, name: u.username };
  } catch {
    return null;
  }
}
