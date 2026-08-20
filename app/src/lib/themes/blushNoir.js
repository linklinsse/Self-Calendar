/**
 * blushNoir.js — "Blush Noir" dark theme with dusty rose accents.
 * The default Self Calendar palette.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const blushNoir = {
  id:   'blushNoir',
  name: 'Blush Noir',
  dark: true,

  bgBase:    '#0d0d12',
  bgSurface: '#13131a',
  bgCard:    '#1a1a24',
  bgRaised:  '#21212e',

  accent:     '#f4b8c8',
  accentDim:  '#c4809a',
  accentGlow: 'rgba(244,184,200,0.16)',
  accentBg:   'rgba(244,184,200,0.07)',

  border:     'rgba(244,184,200,0.10)',
  borderSoft: 'rgba(244,184,200,0.05)',

  text1: '#f0eaf2',
  text2: '#a090a4',
  text3: '#585060',

  shadowCard: '0 4px 24px rgba(0,0,0,0.45)',
  shadowGlow: '0 0 48px rgba(244,184,200,0.12)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
