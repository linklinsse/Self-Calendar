/**
 * electricYellow.js — "Electric" dark theme with vivid #FAFA33 accents.
 *
 * Deep near-black background with subtle warm undertones.
 * The accent is a pure electric yellow that pops on dark surfaces.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const electricYellow = {
  id:   'electricYellow',
  name: 'Electric',
  dark: true,

  bgBase:    '#0c0c08',  // very dark with a faint warm tint
  bgSurface: '#14140c',
  bgCard:    '#1c1c10',
  bgRaised:  '#242416',

  accent:     '#FAFA33',  // electric yellow
  accentDim:  '#c8c800',  // muted golden
  accentGlow: 'rgba(250,250,51,0.20)',
  accentBg:   'rgba(250,250,51,0.07)',

  border:     'rgba(250,250,51,0.14)',
  borderSoft: 'rgba(250,250,51,0.06)',

  text1: '#f5f5e0',  // warm near-white
  text2: '#a8a870',  // warm mid-tone
  text3: '#5a5a30',  // muted olive

  shadowCard: '0 4px 24px rgba(0,0,0,0.55)',
  shadowGlow: '0 0 48px rgba(250,250,51,0.16)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
