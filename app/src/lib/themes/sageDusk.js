/**
 * sageDusk.js — "Sage Dusk" dark theme with mint-green accents.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const sageDusk = {
  id:   'sageDusk',
  name: 'Sage Dusk',
  dark: true,

  bgBase:    '#0e1210',
  bgSurface: '#141a16',
  bgCard:    '#1b231d',
  bgRaised:  '#222d24',

  accent:     '#b8f0c8',
  accentDim:  '#7ab890',
  accentGlow: 'rgba(184,240,200,0.14)',
  accentBg:   'rgba(184,240,200,0.06)',

  border:     'rgba(184,240,200,0.10)',
  borderSoft: 'rgba(184,240,200,0.05)',

  text1: '#eaf2ec',
  text2: '#90a498',
  text3: '#4e5e52',

  shadowCard: '0 4px 24px rgba(0,0,0,0.45)',
  shadowGlow: '0 0 48px rgba(184,240,200,0.10)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
