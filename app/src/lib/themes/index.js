/**
 * themes/index.js — Theme registry.
 *
 * ▶  To add a new theme:
 *    1. Create  src/lib/themes/myTheme.js  (copy any existing theme file)
 *    2. Import and add it to THEMES below
 *    3. Set VITE_THEME=myTheme in .env.local (or pick it in the ThemePicker UI)
 *
 * The active theme is resolved at startup in App.svelte:
 *   import { resolveTheme, applyTheme } from './lib/themes/index.js';
 *   onMount(() => applyTheme(resolveTheme()));
 */

import { blushNoir }        from './blushNoir.js';
import { sageDusk }         from './sageDusk.js';
import { midnightInk }      from './midnightInk.js';
import { oceanBreeze }      from './oceanBreeze.js';
import { electricYellow }   from './electricYellow.js';

// ── Registry ──────────────────────────────────────────────────
// Keyed by theme id — same id used in VITE_THEME env var.
export const THEMES = {
  // ── Dark themes ──────────────────────────
  blushNoir,
  sageDusk,
  midnightInk,
  oceanBreeze,
  electricYellow,
};

/** Ordered list for the ThemePicker UI. */
export const THEME_LIST = Object.values(THEMES);

// ── Active theme store (runtime switching) ────────────────────
import { writable } from 'svelte/store';
import { DEFAULT_THEME_ID } from '../config.js';

const STORAGE_KEY = 'sc_theme';

// Guard against non-browser environments (SSR, test runners).
const _storage = typeof localStorage !== 'undefined' ? localStorage : null;

/**
 * The currently active theme id.
 * Persisted to localStorage so it survives page reloads.
 * @type {import('svelte/store').Writable<string>}
 */
export const activeThemeId = writable(
  _storage?.getItem(STORAGE_KEY) ?? DEFAULT_THEME_ID
);

// Persist changes to localStorage
activeThemeId.subscribe(id => _storage?.setItem(STORAGE_KEY, id));

/**
 * Resolve the theme object for a given id.
 * Falls back to blushNoir if the id is unknown.
 * @param {string} [id]
 * @returns {object} theme
 */
export function resolveTheme(id) {
  return THEMES[id ?? DEFAULT_THEME_ID] ?? blushNoir;
}

// ── CSS injection ─────────────────────────────────────────────

/**
 * Inject a theme's values as CSS custom properties on :root.
 * Safe to call multiple times — later calls overwrite earlier ones.
 * @param {object} theme
 */
export function applyTheme(theme) {
  const root = document.documentElement;
  const map = {
    '--bg':           theme.bgBase,
    '--bg-surf':      theme.bgSurface,
    '--bg-card':      theme.bgCard,
    '--bg-raised':    theme.bgRaised,
    '--acc':          theme.accent,
    '--acc-dim':      theme.accentDim,
    '--acc-glow':     theme.accentGlow,
    '--acc-bg':       theme.accentBg,
    '--bdr':          theme.border,
    '--bdr-soft':     theme.borderSoft,
    '--t1':           theme.text1,
    '--t2':           theme.text2,
    '--t3':           theme.text3,
    '--cat-personal': theme.catPersonal,
    '--cat-work':     theme.catWork,
    '--cat-health':   theme.catHealth,
    '--cat-social':   theme.catSocial,
    '--cat-travel':   theme.catTravel,
    '--f-display':    theme.fontDisplay,
    '--f-body':       theme.fontBody,
    '--f-mono':       theme.fontMono,
    '--fs-xs':        theme.fontSizeXs,
    '--fs-sm':        theme.fontSizeSm,
    '--fs-md':        theme.fontSizeMd,
    '--fs-lg':        theme.fontSizeLg,
    '--fs-xl':        theme.fontSizeXl,
    '--fs-xxl':       theme.fontSizeXxl,
    '--r-s':          theme.radiusSm,
    '--r-m':          theme.radiusMd,
    '--r-l':          theme.radiusLg,
    '--r-xl':         theme.radiusXl,
    '--shadow-card':  theme.shadowCard,
    '--shadow-glow':  theme.shadowGlow,
  };
  for (const [prop, val] of Object.entries(map)) {
    root.style.setProperty(prop, val);
  }
  // Set the browser's color-scheme so native form elements (scrollbars,
  // date-pickers, selects) render in the right mode.
  root.style.colorScheme = theme.dark === false ? 'light' : 'dark';
}
