/**
 * tokens.js — Design tokens shared across all themes.
 *
 * These values are spread into every theme object so you only
 * need to override what you actually want to change.
 *
 * Font stacks use system fonts only — no external requests, works offline.
 * To use a web font: add a <link> in index.html and replace the value below.
 */

/** Font family stacks */
export const FONTS = {
  /** Display font — logo, headings, modal titles. */
  fontDisplay: "Georgia, 'Times New Roman', serif",

  /**
   * Body font — all UI text, labels, inputs, buttons.
   * Resolves to the OS native font on every platform.
   *   macOS/iOS → San Francisco
   *   Windows   → Segoe UI
   *   Android   → Roboto
   *   Linux     → DejaVu / Noto Sans
   */
  fontBody: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",

  /** Mono font — time labels, hex values, code. */
  fontMono: "'SF Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",
};

/**
 * Font size scale.
 * Increase ALL values here to scale the entire UI uniformly.
 */
export const SIZES = {
  fontSizeXs:  '13px',  // tiny labels, timestamps
  fontSizeSm:  '15px',  // secondary text, pills, captions
  fontSizeMd:  '16px',  // default body text
  fontSizeLg:  '19px',  // subheadings, section titles
  fontSizeXl:  '24px',  // topbar period, modal headings
  fontSizeXxl: '34px',  // display / logo
};

/**
 * Border radius scale.
 */
export const RADII = {
  radiusSm: '8px',
  radiusMd: '14px',
  radiusLg: '20px',
  radiusXl: '28px',
};

/**
 * Default category colours — the same across all palettes
 * (categories are user-defined, so their colours are stored per-event,
 * not in the theme, but these are the palette starting points).
 */
export const CAT_COLORS = {
  catPersonal: '#f4b8c8',
  catWork:     '#b8c9f4',
  catHealth:   '#b8f4d4',
  catSocial:   '#f4d8b8',
  catTravel:   '#d8b8f4',
};
