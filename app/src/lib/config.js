/**
 * config.js — Centralised environment configuration.
 *
 * Priority: window.__ENV__ (runtime, injected by docker-entrypoint.sh)
 *           → import.meta.env (build-time VITE_* vars)
 *           → hardcoded defaults
 *
 * Use window.__ENV__ in production Docker deployments so vars can change
 * without rebuilding the image. VITE_* vars still work for local dev.
 */

const buildEnv = (typeof import.meta !== 'undefined' && import.meta.env) ?? {};
const runtimeEnv = (typeof window !== 'undefined' && window.__ENV__) ?? {};

// Prefer runtime value if present and non-empty, else fall back to build-time.
function get(runtimeKey, buildKey, fallback) {
  const rv = runtimeEnv[runtimeKey];
  if (rv !== undefined && rv !== '') return rv;
  return buildEnv[buildKey] ?? fallback;
}

// ── API ──────────────────────────────────────────────────────

/** Backend API base URL (no trailing slash). */
export const API_BASE_URL = get('API_BASE_URL', 'VITE_API_BASE_URL', 'http://localhost:3000/api');

/**
 * When true, the app runs entirely on sample data — no backend needed.
 * Set MOCK_MODE=false (Docker) or VITE_MOCK_MODE=false (.env.local) to use a real server.
 */
export const MOCK_MODE = get('MOCK_MODE', 'VITE_MOCK_MODE', 'true') !== 'false';

// ── Theme ─────────────────────────────────────────────────────

/**
 * Active theme key. Must match a key in src/lib/themes/index.js.
 * Change via THEME (Docker) or VITE_THEME (.env.local), or via the ThemePicker UI.
 */
export const DEFAULT_THEME_ID = get('THEME', 'VITE_THEME', 'blushNoir');

// ── App ───────────────────────────────────────────────────────

/** Application name shown in the browser tab and login screen. */
export const APP_NAME = get('APP_NAME', 'VITE_APP_NAME', 'Self Calendar');

/**
 * Default calendar view after login: 'month' | 'week' | 'day'.
 * @type {'month'|'week'|'day'}
 */
export const DEFAULT_VIEW = get('DEFAULT_VIEW', 'VITE_DEFAULT_VIEW', 'month');

/**
 * First day of week: 0=Sunday, 1=Monday, 6=Saturday.
 * @type {number}
 */
export const FIRST_DAY_OF_WEEK = Number(get('FIRST_DAY_OF_WEEK', 'VITE_FIRST_DAY_OF_WEEK', '1'));

/** Locale string for Intl date formatting (e.g. 'en-US', 'fr-FR'). */
export const LOCALE = get('LOCALE', 'VITE_LOCALE', 'fr-FR');
