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

/**
 * Public server capabilities, from GET /auth/config. Unauthenticated.
 *
 * Used by the login screen to decide whether to offer registration at all:
 * the server closes it with USER_CREATION=False (which the README tells
 * operators to do once they have an account), and without asking there is
 * no way for the client to know.
 *
 * Falls back to allowing registration if the call fails, so an older API or
 * a transient error degrades to the previous behaviour rather than locking
 * a first-run user out of creating their account.
 *
 * @returns {Promise<{ user_creation: boolean }>}
 */
export async function fetchAuthConfig() {
  try {
    const cfg = await api.get('/auth/config');
    return { user_creation: cfg?.user_creation !== false };
  } catch {
    return { user_creation: true };
  }
}

/**
 * Change the signed-in user's password.
 *
 * The API bumps `token_version` on success, which invalidates every token
 * issued before this call — including this session's own. That is the point
 * (a leaked password's remedy has to evict whoever stole it), but it means
 * the caller must re-authenticate immediately afterwards or every subsequent
 * request 401s. See changePassword in stores/index.js, which does that.
 *
 * @param {string} oldPassword
 * @param {string} newPassword
 * @returns {Promise<object>} the updated user
 */
export async function changePasswordRequest(oldPassword, newPassword) {
  return api.patch('/user/password', {
    old_password: oldPassword,
    new_password: newPassword,
  }, {
    // A 401 here means "the old password you typed is wrong", not "your
    // session expired" — without this the global interceptor would sign the
    // user out for a typo.
    skip401Logout: true,
  });
}


/**
 * Mint a long-lived refresh token for the signed-in user.
 *
 * Only the Android widget needs one: it renders for weeks without the user
 * necessarily opening the app, while an access token lasts a day, so without
 * this it silently froze on stale data once its token expired.
 *
 * Returns null rather than throwing — a server too old to have the endpoint,
 * or a transient failure, should degrade to the previous behaviour (widget
 * works until the access token expires) instead of breaking login.
 *
 * @returns {Promise<string|null>}
 */
export async function fetchRefreshToken() {
  try {
    const res = await api.post('/auth/refresh-token');
    return res?.refresh_token ?? null;
  } catch {
    return null;
  }
}
