/**
 * config.js — Centralised environment configuration.
 *
 * Priority: window.__ENV__ (runtime, injected by docker-entrypoint.sh)
 *           → import.meta.env (build-time vars)
 *           → hardcoded defaults
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

/** Backend API base URL (no trailing slash). */
export const API_BASE_URL = get('API_BASE_URL', 'https://sc.linklinsse.dk:3637');

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
