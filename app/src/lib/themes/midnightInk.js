/**
 * midnightInk.js — "Midnight Ink" deep dark theme with lavender accents.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const midnightInk = {
  id:   'midnightInk',
  name: 'Midnight Ink',
  dark: true,

  bgBase:    '#09090f',
  bgSurface: '#0f0f18',
  bgCard:    '#161620',
  bgRaised:  '#1e1e2a',

  accent:     '#c8b8f4',
  accentDim:  '#9880d0',
  accentGlow: 'rgba(200,184,244,0.14)',
  accentBg:   'rgba(200,184,244,0.06)',

  border:     'rgba(200,184,244,0.10)',
  borderSoft: 'rgba(200,184,244,0.05)',

  text1: '#edeaf5',
  text2: '#9890b0',
  text3: '#524e68',

  shadowCard: '0 4px 24px rgba(0,0,0,0.5)',
  shadowGlow: '0 0 48px rgba(200,184,244,0.10)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
