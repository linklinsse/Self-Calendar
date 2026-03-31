/**
 * sunsetAmber.js — "Sunset Amber" dark theme with warm orange-gold accents.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const sunsetAmber = {
  id:   'sunsetAmber',
  name: 'Sunset Amber',
  dark: true,

  bgBase:    '#100d08',
  bgSurface: '#1a1510',
  bgCard:    '#221d15',
  bgRaised:  '#2c251a',

  accent:     '#f0b84a',
  accentDim:  '#c0882a',
  accentGlow: 'rgba(240,184,74,0.16)',
  accentBg:   'rgba(240,184,74,0.07)',

  border:     'rgba(240,184,74,0.12)',
  borderSoft: 'rgba(240,184,74,0.06)',

  text1: '#f5efe0',
  text2: '#a89070',
  text3: '#605040',

  shadowCard: '0 4px 24px rgba(0,0,0,0.5)',
  shadowGlow: '0 0 48px rgba(240,184,74,0.12)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
