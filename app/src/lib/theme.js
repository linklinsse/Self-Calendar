/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║  SELF CALENDAR — THEME                                       ║
 * ║                                                              ║
 * ║  Edit THIS file to change the entire look of the app.       ║
 * ║  All values are injected as CSS custom properties on :root   ║
 * ║  by App.svelte at startup via applyTheme().                  ║
 * ║                                                              ║
 * ║  To switch palette: change ACTIVE_THEME at the bottom.       ║
 * ║  To change fonts: update fontDisplay / fontBody / fontMono.  ║
 * ║  To change sizes: update the fontSize* values.               ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * System font stacks — no external requests, works offline.
 * If you want a web font, add a <link> in index.html then
 * replace the font string below (e.g. "'Inter', system-ui, sans-serif").
 */

// ── Shared font stacks (used by all palettes) ─────────────────
const FONTS = {
  /**
   * Display font — logo, large headings, modal titles.
   * Georgia gives a refined editorial feel without any download.
   * Alternatives: "'Playfair Display', Georgia, serif"  (Google Font)
   */
  fontDisplay: "Georgia, 'Times New Roman', serif",

  /**
   * Body font — all UI text, labels, inputs, buttons.
   * system-ui resolves to the OS native font on every platform:
   *   macOS/iOS  → San Francisco
   *   Windows    → Segoe UI
   *   Android    → Roboto
   *   Linux      → DejaVu / Noto Sans
   * Alternatives: "'Inter', system-ui, sans-serif"  (Google Font)
   */
  fontBody: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",

  /**
   * Mono font — time labels, hex values, code snippets.
   * Alternatives: "'JetBrains Mono', monospace"  (Google Font)
   */
  fontMono: "'SF Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",
};

// ── Shared font sizes ─────────────────────────────────────────
// All sizes relative to root. Increase ALL values here to make the
// entire app larger — no individual component hunting required.
const SIZES = {
  fontSizeXs:  '13px',   // tiny labels, timestamps
  fontSizeSm:  '15px',   // secondary text, pills, captions
  fontSizeMd:  '16px',   // default body text — the most-used size
  fontSizeLg:  '19px',   // subheadings, section titles
  fontSizeXl:  '24px',   // topbar period label, modal headings
  fontSizeXxl: '34px',   // display / logo
};

// ── Palette: Blush Noir (default) ────────────────────────────
const blushNoir = {
  name: 'Blush Noir',

  /* Backgrounds — darkest to lightest */
  bgBase:    '#0d0d12',
  bgSurface: '#13131a',
  bgCard:    '#1a1a24',
  bgRaised:  '#21212e',

  /* Accent */
  accent:     '#f4b8c8',
  accentDim:  '#c4809a',
  accentGlow: 'rgba(244,184,200,0.16)',
  accentBg:   'rgba(244,184,200,0.07)',

  /* Borders */
  border:     'rgba(244,184,200,0.10)',
  borderSoft: 'rgba(244,184,200,0.05)',

  /* Text */
  text1: '#f0eaf2',
  text2: '#a090a4',
  text3: '#585060',

  /* Category colours */
  catPersonal: '#f4b8c8',
  catWork:     '#b8c9f4',
  catHealth:   '#b8f4d4',
  catSocial:   '#f4d8b8',
  catTravel:   '#d8b8f4',

  /* Radii */
  radiusSm: '8px',
  radiusMd: '14px',
  radiusLg: '20px',
  radiusXl: '28px',

  /* Shadows */
  shadowCard: '0 4px 24px rgba(0,0,0,0.45)',
  shadowGlow: '0 0 48px rgba(244,184,200,0.12)',

  ...FONTS,
  ...SIZES,
};

// ── Palette: Sage Dusk ────────────────────────────────────────
const sageDusk = {
  name: 'Sage Dusk',
  bgBase: '#0e1210', bgSurface: '#141a16', bgCard: '#1b231d', bgRaised: '#222d24',
  accent: '#b8f0c8', accentDim: '#7ab890',
  accentGlow: 'rgba(184,240,200,0.14)', accentBg: 'rgba(184,240,200,0.06)',
  border: 'rgba(184,240,200,0.10)', borderSoft: 'rgba(184,240,200,0.05)',
  text1: '#eaf2ec', text2: '#90a498', text3: '#4e5e52',
  catPersonal: '#f4b8c8', catWork: '#b8c9f4', catHealth: '#b8f4d4', catSocial: '#f4d8b8', catTravel: '#d8b8f4',
  radiusSm: '8px', radiusMd: '14px', radiusLg: '20px', radiusXl: '28px',
  shadowCard: '0 4px 24px rgba(0,0,0,0.45)', shadowGlow: '0 0 48px rgba(184,240,200,0.10)',
  ...FONTS, ...SIZES,
};

// ── Palette: Midnight Ink ─────────────────────────────────────
const midnightInk = {
  name: 'Midnight Ink',
  bgBase: '#09090f', bgSurface: '#0f0f18', bgCard: '#161620', bgRaised: '#1e1e2a',
  accent: '#c8b8f4', accentDim: '#9880d0',
  accentGlow: 'rgba(200,184,244,0.14)', accentBg: 'rgba(200,184,244,0.06)',
  border: 'rgba(200,184,244,0.10)', borderSoft: 'rgba(200,184,244,0.05)',
  text1: '#edeaf5', text2: '#9890b0', text3: '#524e68',
  catPersonal: '#f4b8c8', catWork: '#b8c9f4', catHealth: '#b8f4d4', catSocial: '#f4d8b8', catTravel: '#d8b8f4',
  radiusSm: '8px', radiusMd: '14px', radiusLg: '20px', radiusXl: '28px',
  shadowCard: '0 4px 24px rgba(0,0,0,0.5)', shadowGlow: '0 0 48px rgba(200,184,244,0.10)',
  ...FONTS, ...SIZES,
};

// ═══════════════════════════════════════════════════════════════
// ▶  CHANGE PALETTE HERE
// ═══════════════════════════════════════════════════════════════
export const ACTIVE_THEME = blushNoir;

/**
 * Injects all theme values as CSS custom properties onto :root.
 * Called once in App.svelte onMount().
 */
export function applyTheme(theme = ACTIVE_THEME) {
  const root = document.documentElement;
  const map = {
    '--bg':          theme.bgBase,
    '--bg-surf':     theme.bgSurface,
    '--bg-card':     theme.bgCard,
    '--bg-raised':   theme.bgRaised,
    '--acc':         theme.accent,
    '--acc-dim':     theme.accentDim,
    '--acc-glow':    theme.accentGlow,
    '--acc-bg':      theme.accentBg,
    '--bdr':         theme.border,
    '--bdr-soft':    theme.borderSoft,
    '--t1':          theme.text1,
    '--t2':          theme.text2,
    '--t3':          theme.text3,
    '--cat-personal':theme.catPersonal,
    '--cat-work':    theme.catWork,
    '--cat-health':  theme.catHealth,
    '--cat-social':  theme.catSocial,
    '--cat-travel':  theme.catTravel,
    '--f-display':   theme.fontDisplay,
    '--f-body':      theme.fontBody,
    '--f-mono':      theme.fontMono,
    '--fs-xs':       theme.fontSizeXs,
    '--fs-sm':       theme.fontSizeSm,
    '--fs-md':       theme.fontSizeMd,
    '--fs-lg':       theme.fontSizeLg,
    '--fs-xl':       theme.fontSizeXl,
    '--fs-xxl':      theme.fontSizeXxl,
    '--r-s':         theme.radiusSm,
    '--r-m':         theme.radiusMd,
    '--r-l':         theme.radiusLg,
    '--r-xl':        theme.radiusXl,
    '--shadow-card': theme.shadowCard,
    '--shadow-glow': theme.shadowGlow,
  };
  for (const [prop, val] of Object.entries(map)) {
    root.style.setProperty(prop, val);
  }
}
