/**
 * api.js — HTTP client. Reads all configuration from config.js.
 */
import { API_BASE_URL, MOCK_MODE } from '../config.js';

export { API_BASE_URL, MOCK_MODE };

const TOKEN_KEY = 'sc_auth_token';
export const setToken = t => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
export const getToken = ()  => localStorage.getItem(TOKEN_KEY);

export class ApiError extends Error {
  constructor(status, message, body = null) {
    super(message); this.name = 'ApiError'; this.status = status; this.body = body;
  }
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
  if ((res.headers.get('content-type') || '').includes('application/json')) data = await res.json();
  if (!res.ok) throw new ApiError(res.status, data?.message || data?.error || res.statusText, data);
  return data;
}

export const api = {
  get:    path       => MOCK_MODE ? Promise.resolve(null) : request(path, 'GET'),
  post:   (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'POST',   b),
  put:    (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'PUT',    b),
  patch:  (path, b)  => MOCK_MODE ? Promise.resolve(null) : request(path, 'PATCH',  b),
  delete: path       => MOCK_MODE ? Promise.resolve(null) : request(path, 'DELETE'),
};
