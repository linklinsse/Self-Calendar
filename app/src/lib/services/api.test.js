/**
 * api.test.js — 401 handling and the silent-refresh retry.
 *
 * The access token lasts 24h and, before this, nothing ever renewed it: a
 * 401 went straight to handle401() and the user was bounced to the login
 * screen daily (see TODO). request() now tries POST /auth/refresh once,
 * using the stored refresh token, and retries the original call before
 * giving up — these tests pin that behaviour and its edge cases (no
 * refresh token, concurrent 401s, and the paths that must never trigger it).
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';

vi.mock('../stores/index.js', () => ({
  logoutUser: vi.fn().mockResolvedValue(undefined),
}));

import { api, setToken, getToken, setRefreshToken, getRefreshToken, ApiError } from './api.js';

function createFakeStorage() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
}

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (h) => (h.toLowerCase() === 'content-type' ? 'application/json' : null) },
    text: async () => JSON.stringify(body),
  };
}

const UNAUTHORIZED = { detail: { error_code: 'INVALID_TOKEN', message: 'expired' } };

beforeEach(() => {
  vi.stubGlobal('localStorage', createFakeStorage());
  vi.stubGlobal('fetch', vi.fn());
});

describe('request() — happy path', () => {
  it('resolves with the parsed body and sends no refresh call', async () => {
    fetch.mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    await expect(api.get('/calendar/')).resolves.toEqual({ ok: true });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});

describe('request() — 401 with a refresh token available', () => {
  it('silently refreshes and retries the original call once', async () => {
    setToken('stale-access-token');
    setRefreshToken('valid-refresh-token');

    fetch
      .mockResolvedValueOnce(jsonResponse(401, UNAUTHORIZED))       // original call
      .mockResolvedValueOnce(jsonResponse(200, 'fresh-access-token')) // POST /auth/refresh
      .mockResolvedValueOnce(jsonResponse(200, [{ id: 'cal-1' }]));   // retried original call

    const data = await api.get('/calendar/');

    expect(data).toEqual([{ id: 'cal-1' }]);
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls[1][0]).toContain('/auth/refresh');
    // The new access token replaces the stale one for the retry and beyond.
    expect(getToken()).toBe('fresh-access-token');
  });

  it('dedupes concurrent 401s into a single refresh call', async () => {
    setToken('stale-access-token');
    setRefreshToken('valid-refresh-token');

    // Keyed by URL (not call order) so the assertions don't depend on which
    // of the two requests happens to resume first after the shared refresh.
    let calendarCalls = 0;
    let categoryCalls = 0;
    fetch.mockImplementation(async (url) => {
      if (url.includes('/auth/refresh')) return jsonResponse(200, 'fresh-access-token');
      if (url.includes('/calendar/')) {
        calendarCalls += 1;
        return calendarCalls === 1 ? jsonResponse(401, UNAUTHORIZED) : jsonResponse(200, { a: 1 });
      }
      if (url.includes('/category/')) {
        categoryCalls += 1;
        return categoryCalls === 1 ? jsonResponse(401, UNAUTHORIZED) : jsonResponse(200, { b: 1 });
      }
      throw new Error(`unexpected fetch to ${url}`);
    });

    const [a, b] = await Promise.all([api.get('/calendar/'), api.get('/category/')]);

    expect(a).toEqual({ a: 1 });
    expect(b).toEqual({ b: 1 });
    const refreshCalls = fetch.mock.calls.filter(([url]) => url.includes('/auth/refresh'));
    expect(refreshCalls).toHaveLength(1);
  });

  it('drops the refresh token when /auth/refresh itself fails, and logs out', async () => {
    setToken('stale-access-token');
    setRefreshToken('dead-refresh-token');

    fetch
      .mockResolvedValueOnce(jsonResponse(401, UNAUTHORIZED)) // original call
      .mockResolvedValueOnce(jsonResponse(401, UNAUTHORIZED)); // POST /auth/refresh also 401s

    await expect(api.get('/calendar/')).rejects.toBeInstanceOf(ApiError);

    expect(getToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    // No third call: the original request is not retried a second time.
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});

describe('request() — 401 with no refresh token stored', () => {
  it('goes straight to the 401 handler without calling /auth/refresh', async () => {
    setToken('stale-access-token');
    // No setRefreshToken call — nothing stored.

    fetch.mockResolvedValueOnce(jsonResponse(401, UNAUTHORIZED));

    await expect(api.get('/calendar/')).rejects.toBeInstanceOf(ApiError);

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(getToken()).toBeNull(); // handle401 cleared it
  });
});

describe('request() — paths and options that must not trigger a refresh retry', () => {
  it('does not retry /auth/login, even with a valid refresh token stored', async () => {
    setRefreshToken('valid-refresh-token');
    fetch.mockResolvedValueOnce(jsonResponse(401, { detail: { error_code: 'INVALID_CREDENTIALS' } }));

    await expect(api.post('/auth/login', { username: 'x', password: 'wrong' }))
      .rejects.toBeInstanceOf(ApiError);

    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('honours skip401Logout: no refresh attempt and the token is left alone', async () => {
    setToken('some-token');
    setRefreshToken('valid-refresh-token');
    fetch.mockResolvedValueOnce(jsonResponse(401, { detail: { message: 'wrong old password' } }));

    await expect(
      api.patch('/user/password', { old_password: 'x', new_password: 'y' }, { skip401Logout: true })
    ).rejects.toBeInstanceOf(ApiError);

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(getToken()).toBe('some-token'); // not cleared — this 401 wasn't a session death
  });
});
