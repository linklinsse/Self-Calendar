/**
 * themes/index.js — Theme registry.
 *
 * ▶  To add a new theme:
 *    1. Copy any existing theme file, e.g. src/lib/themes/myTheme.js
 *    2. Import it and add it to THEME_LIST below — that is the only edit
 *    3. Optionally set VITE_THEME=myTheme as the default, or just pick it
 *       in the ThemePicker
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
import { unicorn }          from './unicorn.js';

// ── Registry ──────────────────────────────────────────────────
//
// THE ARRAY IS THE SOURCE OF TRUTH. Order here is the order shown in the
// ThemePicker, so it is a design decision rather than a side effect of
// object key ordering. THEMES below is derived from it, so adding a theme
// is one line in one place and the two can never disagree.

/** @type {object[]} Ordered; drives the ThemePicker UI. */
export const THEME_LIST = [
  // ── Dark ──────────────────────────
  blushNoir,
  electricYellow,
  midnightInk,
  oceanBreeze,
  sageDusk,
  // ── Light ─────────────────────────
  unicorn,
];

/**
 * Keys every theme must define. Everything else (fonts, sizes, radii,
 * category colours) comes from tokens.js via the spread at the bottom of
 * each theme file, so only the palette is listed here.
 */
const REQUIRED_KEYS = [
  'id', 'name',
  'bgBase', 'bgSurface', 'bgCard', 'bgRaised',
  'accent', 'accentDim', 'accentGlow', 'accentBg',
  'border', 'borderSoft',
  'text1', 'text2', 'text3',
  'shadowCard', 'shadowGlow',
];

// Validate at import time, and only in dev. A theme missing a key does not
// throw — it silently sets a CSS variable to `undefined`, which browsers
// ignore, so the app keeps the *previous* theme's value for that one
// property. The result is a half-applied theme that looks like a styling
// bug rather than a typo, which is a genuinely annoying hour to debug.
if (import.meta.env?.DEV) {
  const seen = new Set();
  for (const theme of THEME_LIST) {
    const missing = REQUIRED_KEYS.filter(k => theme?.[k] === undefined);
    if (missing.length) {
      console.error(
        `[themes] "${theme?.id ?? '(no id)'}" is missing: ${missing.join(', ')}`
      );
    }
    if (seen.has(theme?.id)) {
      console.error(`[themes] duplicate id "${theme.id}" — the later one wins`);
    }
    seen.add(theme?.id);
  }
}

/**
 * Keyed by theme id — the same id used in the VITE_THEME env var and
 * persisted to localStorage. Derived from THEME_LIST; do not edit directly.
 * @type {Record<string, object>}
 */
export const THEMES = Object.fromEntries(THEME_LIST.map(t => [t.id, t]));

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
