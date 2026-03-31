/**
 * config.js — Centralised environment configuration.
 *
 * All VITE_* environment variables are read here. Components should
 * import from this file rather than accessing import.meta.env directly.
 * This makes it trivial to find and change any configuration value.
 *
 * Variables are set in .env (committed defaults) or .env.local (secrets,
 * gitignored). See .env for the full list of available variables.
 */

const env = (typeof import.meta !== 'undefined' && import.meta.env) ?? {};

// ── API ──────────────────────────────────────────────────────

/** Backend API base URL (no trailing slash). */
export const API_BASE_URL = env.VITE_API_BASE_URL ?? 'http://localhost:3000/api';

/**
 * When true, the app runs entirely on sample data — no backend needed.
 * Set VITE_MOCK_MODE=false in .env.local to use a real server.
 */
export const MOCK_MODE = (env.VITE_MOCK_MODE ?? 'true') !== 'false';

// ── Theme ─────────────────────────────────────────────────────

/**
 * Active theme key. Must match a key in src/lib/themes/index.js.
 * Change via VITE_THEME in .env.local, or at runtime via the ThemePicker UI.
 */
export const DEFAULT_THEME_ID = env.VITE_THEME ?? 'blushNoir';

// ── App ───────────────────────────────────────────────────────

/** Application name shown in the browser tab and login screen. */
export const APP_NAME = env.VITE_APP_NAME ?? 'Self Calendar';

/**
 * Default calendar view after login: 'month' | 'week' | 'day'.
 * @type {'month'|'week'|'day'}
 */
export const DEFAULT_VIEW = (env.VITE_DEFAULT_VIEW ?? 'month');

/**
 * First day of week: 0=Sunday, 1=Monday, 6=Saturday.
 * @type {number}
 */
export const FIRST_DAY_OF_WEEK = Number(env.VITE_FIRST_DAY_OF_WEEK ?? 1);

/** Locale string for Intl date formatting (e.g. 'en-US', 'fr-FR'). */
export const LOCALE = env.VITE_LOCALE ?? 'en-US';
