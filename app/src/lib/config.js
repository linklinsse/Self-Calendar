/**
 * config.js — Centralised environment configuration.
 *
 * Priority: window.__ENV__ (runtime, injected by docker-entrypoint.sh)
 *           → import.meta.env (build-time vars)
 *           → hardcoded defaults
 *
 * API_BASE_URL additionally honours a per-browser override saved from the
 * login screen, which takes priority over all of the above — see below.
 *
 * Use window.__ENV__ in production Docker deployments so vars can change
 * without rebuilding the image. For local dev, prefix the bare name with
 * VITE_ in .env.local (e.g. VITE_MOCK_MODE=false) — the get() helper
 * looks up VITE_<KEY> in import.meta.env automatically.
 */

const buildEnv = (typeof import.meta !== 'undefined' && import.meta.env) ?? {};
const runtimeEnv = (typeof window !== 'undefined' && window.__ENV__) ?? {};

// Prefer runtime value if present and non-empty, else fall back to build-time.
// Build-time vars must be prefixed VITE_ in .env.local (Vite requirement).
function get(key, fallback) {
  const rv = runtimeEnv[key];
  if (rv !== undefined && rv !== '') return rv;
  return buildEnv[`VITE_${key}`] ?? fallback;
}

// ── API ──────────────────────────────────────────────────────

/** localStorage key holding the user's own backend URL, if they set one. */
const API_BASE_URL_KEY = 'sc_api_base_url';

/**
 * Backend API base URL as configured by whoever built or deployed this copy
 * (window.__ENV__ → VITE_API_BASE_URL → same-origin).
 *
 * Falls back to same-origin — NOT a specific deployment's URL — so a broken
 * runtime-injection setup fails obviously (network error) instead of
 * silently posting credentials to someone else's server.
 */
export const DEFAULT_API_BASE_URL = get(
  'API_BASE_URL',
  typeof window !== 'undefined' ? window.location.origin : ''
);

/**
 * Normalise a user-supplied backend URL, or return null if it isn't usable.
 *
 * Only http and https are accepted. This matters: the value is interpolated
 * into every fetch() the app makes, so allowing arbitrary schemes here would
 * turn a settings field into a script-execution vector (`javascript:…`) for
 * anyone who could talk a user into pasting one in.
 *
 * @param {string} raw
 * @returns {string|null} origin + path, no trailing slash
 */
export function normaliseApiBaseUrl(raw) {
  const trimmed = (raw ?? '').trim();
  if (!trimmed) return null;

  let url;
  try {
    url = new URL(trimmed);
  } catch {
    // Bare host like "192.168.1.10:8787" — a very natural thing to type for
    // a self-hosted box, so try it as http rather than rejecting outright.
    //
    // Only when there is no scheme already: prepending to something like
    // "http://" (an incomplete paste) yields "http://http://", which parses
    // happily as the host "http" and would send every request to a
    // nonexistent server with no hint as to why.
    if (trimmed.includes('://')) return null;
    try {
      url = new URL(`http://${trimmed}`);
    } catch {
      return null;
    }
  }

  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null;

  // Keep any sub-path (some deployments mount the API under /api), drop the
  // trailing slash so callers can concatenate paths that start with one.
  const path = url.pathname.replace(/\/+$/, '');
  return `${url.origin}${path}`;
}

/**
 * The override saved from the login screen, if any and if still valid.
 *
 * Re-validated on read rather than trusted: localStorage is editable by
 * hand and persists across app versions.
 */
function readOverride() {
  if (typeof localStorage === 'undefined') return null;
  try {
    const stored = localStorage.getItem(API_BASE_URL_KEY);
    return stored ? normaliseApiBaseUrl(stored) : null;
  } catch {
    return null; // private mode / storage disabled
  }
}

/** True when this browser is pointed at a backend the build didn't specify. */
export const IS_API_BASE_URL_OVERRIDDEN = readOverride() !== null;

/**
 * Effective backend API base URL (no trailing slash).
 *
 * Resolved once at module load, deliberately. Switching backends invalidates
 * the session token, every loaded store and the Android widget's cached
 * data, so the only coherent way to apply a change is a full reload — which
 * setApiBaseUrl() does. Reading this live per-request would instead allow a
 * half-switched state where some calls go to the old server and some to the
 * new one.
 */
export const API_BASE_URL = readOverride() ?? DEFAULT_API_BASE_URL;

/**
 * Point this browser at a different backend and reload.
 *
 * The reload is not optional cleanliness — see API_BASE_URL above. The
 * caller does not get control back.
 *
 * @param {string} raw
 * @throws if the URL is unusable
 */
export function setApiBaseUrl(raw) {
  const normalised = normaliseApiBaseUrl(raw);
  if (!normalised) throw new Error('Enter a valid http:// or https:// address.');

  localStorage.setItem(API_BASE_URL_KEY, normalised);
  // The old server's token means nothing to the new one, and leaving it
  // behind produces a confusing 401 on first load instead of a login screen.
  localStorage.removeItem('sc_auth_token');
  window.location.reload();
}

/** Forget the override and go back to whatever this build was configured with. */
export function resetApiBaseUrl() {
  localStorage.removeItem(API_BASE_URL_KEY);
  localStorage.removeItem('sc_auth_token');
  window.location.reload();
}

// ── Theme ─────────────────────────────────────────────────────

/**
 * Active theme key. Must match a key in src/lib/themes/index.js.
 * Change via THEME (Docker) or VITE_THEME (.env.local), or via the ThemePicker UI.
 */
export const DEFAULT_THEME_ID = get('THEME', 'blushNoir');

// ── App ───────────────────────────────────────────────────────

/** Application name shown in the browser tab and login screen. */
export const APP_NAME = get('APP_NAME', 'Self Calendar');

/**
 * Default calendar view after login: 'month' | 'week' | 'day'.
 * @type {'month'|'week'|'day'}
 */
export const DEFAULT_VIEW = get('DEFAULT_VIEW', 'month');

/**
 * First day of week: 0=Sunday, 1=Monday, 6=Saturday.
 * @type {number}
 */
export const FIRST_DAY_OF_WEEK = Number(get('FIRST_DAY_OF_WEEK', '1'));

/** Locale string for Intl date formatting (e.g. 'en-US', 'fr-FR'). */
export const LOCALE = get('LOCALE', 'fr-FR');

/**
 * Hour display format: '12' for AM/PM, '24' for 24-hour.
 * Affects time labels in Day/Week views and the time inputs in the event panel.
 * @type {'12'|'24'}
 */
export const HOUR_FORMAT = get('HOUR_FORMAT', '24');
