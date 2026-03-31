/**
 * lightClean.js — "Light Clean" bright theme with slate-blue accents.
 *
 * A crisp, minimal light mode. Backgrounds go from near-white to white,
 * borders are subtle grey, text is near-black. The accent is a calm
 * slate-blue that reads well on light backgrounds.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const lightClean = {
  id:   'lightClean',
  name: 'Light',
  dark: false,

  bgBase:    '#f4f5f7',  // page background — very light grey
  bgSurface: '#ffffff',  // sidebar, topbar
  bgCard:    '#f0f1f4',  // cards, modals
  bgRaised:  '#e8eaee',  // inputs, dropdowns

  accent:     '#4a6fa5',  // slate-blue
  accentDim:  '#2e4e80',  // deeper blue on hover
  accentGlow: 'rgba(74,111,165,0.14)',
  accentBg:   'rgba(74,111,165,0.08)',

  border:     'rgba(0,0,0,0.12)',
  borderSoft: 'rgba(0,0,0,0.06)',

  text1: '#1a1d24',  // near-black
  text2: '#555c6e',  // mid-grey
  text3: '#9099aa',  // light grey

  shadowCard: '0 2px 16px rgba(0,0,0,0.10)',
  shadowGlow: '0 0 32px rgba(74,111,165,0.10)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
