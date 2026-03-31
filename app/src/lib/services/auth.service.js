/**
 * auth.service.js — Authentication: login (username), register, logout, getMe.
 *
 * POST /auth/login    { username, password } → { token, user }
 * POST /auth/register { username, password } → { token, user }
 * POST /auth/logout
 * GET  /auth/me                              → User
 */
import { api, setToken, getToken, MOCK_MODE } from './api.js';

/** @typedef {{ id:string, username:string, name:string, avatar?:string }} User */

const MOCK_USER = { id:'user-1', username:'demo', name:'Demo User', avatar: null };

/** Login with username + password. */
export async function login(username, password) {
  if (MOCK_MODE) {
    await new Promise(r => setTimeout(r, 400));
    setToken('mock-token');
    return MOCK_USER;
  }
  const { token, user } = await api.post('/auth/login', { username, password });
  setToken(token);
  return user;
}

/** Register a new account. */
export async function register(username, password) {
  if (MOCK_MODE) {
    await new Promise(r => setTimeout(r, 500));
    setToken('mock-token');
    return { ...MOCK_USER, username };
  }
  const { token, user } = await api.post('/auth/register', { username, password });
  setToken(token);
  return user;
}

/** Log out. Clears local token. */
export async function logout() {
  if (!MOCK_MODE) await api.post('/auth/logout').catch(() => {});
  setToken(null);
}

/** Fetch the current authenticated user (or null). */
export async function getMe() {
  if (MOCK_MODE) return getToken() ? MOCK_USER : null;
  try { return await api.get('/auth/me'); } catch { return null; }
}
