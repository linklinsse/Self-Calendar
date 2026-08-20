/**
 * unicorn.js — "Unicorn": the deliberately silly one.
 *
 * A light, pastel, high-saturation palette. The only light theme in the set,
 * so it is also the one that exercises `dark: false` — if native form
 * controls, scrollbars or date pickers ever render wrong in light mode, this
 * is the theme that shows it.
 *
 * Being playful does not exempt it from being readable. Text colours here
 * were picked to stay legible on the pale backgrounds rather than to be as
 * pink as possible:
 *
 *   text1 #3d2450 on bgCard #fff5fc  → contrast ratio ~12.6:1  (WCAG AAA)
 *   text2 #7a4a91 on bgCard #fff5fc  → contrast ratio ~6.4:1   (WCAG AA)
 *   text3 #a878bd on bgCard #fff5fc  → contrast ratio ~3.3:1
 *
 * text3 is used only for decorative and disabled states, where it sits below
 * the 4.5:1 body-text threshold on purpose — the same role it plays in every
 * other theme in this project. Do not use it for anything a user must read.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const unicorn = {
  id:   'unicorn',
  name: 'Unicorn',
  dark: false,

  // Pale lilac through to white, so cards lift off the background without
  // needing heavy borders.
  bgBase:    '#f6eaff',
  bgSurface: '#fdf2ff',
  bgCard:    '#fff5fc',
  bgRaised:  '#ffffff',

  // Magenta-pink accent, dark enough to carry white text on buttons.
  accent:     '#d946a6',
  accentDim:  '#a63384',
  accentGlow: 'rgba(217,70,166,0.20)',
  accentBg:   'rgba(217,70,166,0.09)',

  border:     'rgba(167,80,190,0.22)',
  borderSoft: 'rgba(167,80,190,0.12)',

  text1: '#3d2450',
  text2: '#7a4a91',
  text3: '#a878bd',

  // Softer and more diffuse than the dark themes' shadows — a hard drop
  // shadow on a pale background reads as dirt rather than depth.
  shadowCard: '0 4px 20px rgba(167,80,190,0.16)',
  shadowGlow: '0 0 48px rgba(217,70,166,0.18)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,

  // Rainbow category defaults, overriding the shared pastels. Kept in the
  // same order as CAT_COLORS so the spread above is what gets replaced.
  catPersonal: '#ff6ec7',
  catWork:     '#7c6ef5',
  catHealth:   '#3fd6a0',
  catSocial:   '#ffb03f',
  catTravel:   '#4fc3f7',
};
