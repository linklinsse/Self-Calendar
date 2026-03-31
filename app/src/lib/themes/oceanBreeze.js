/**
 * oceanBreeze.js — "Ocean Breeze" dark theme with cyan accents.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const oceanBreeze = {
  id:   'oceanBreeze',
  name: 'Ocean Breeze',
  dark: true,

  bgBase:    '#090f12',
  bgSurface: '#0f1820',
  bgCard:    '#162029',
  bgRaised:  '#1d2a35',

  accent:     '#7dd8f0',
  accentDim:  '#4aa8c8',
  accentGlow: 'rgba(125,216,240,0.14)',
  accentBg:   'rgba(125,216,240,0.06)',

  border:     'rgba(125,216,240,0.12)',
  borderSoft: 'rgba(125,216,240,0.06)',

  text1: '#e8f4f8',
  text2: '#7898a8',
  text3: '#3e5868',

  shadowCard: '0 4px 24px rgba(0,0,0,0.5)',
  shadowGlow: '0 0 48px rgba(125,216,240,0.10)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
