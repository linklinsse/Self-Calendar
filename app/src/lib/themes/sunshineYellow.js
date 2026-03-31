/**
 * sunshineYellow.js — "Sunshine" warm dark theme with vivid yellow accents.
 *
 * A cosy dark-amber background with golden-yellow highlights.
 * Think candlelight and old parchment — warm, rich, easy on the eyes.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const sunshineYellow = {
  id:   'sunshineYellow',
  name: 'Sunshine',
  dark: true,

  bgBase:    '#110f08',
  bgSurface: '#1c180e',
  bgCard:    '#252010',
  bgRaised:  '#2f2a17',

  accent:     '#f5d020',  // vivid yellow
  accentDim:  '#c8a800',  // golden
  accentGlow: 'rgba(245,208,32,0.18)',
  accentBg:   'rgba(245,208,32,0.08)',

  border:     'rgba(245,208,32,0.14)',
  borderSoft: 'rgba(245,208,32,0.07)',

  text1: '#fdf5d8',  // warm cream
  text2: '#b09a60',  // warm tan
  text3: '#6a5a30',  // muted ochre

  shadowCard: '0 4px 24px rgba(0,0,0,0.50)',
  shadowGlow: '0 0 48px rgba(245,208,32,0.14)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
