/**
 * blossomPink.js — "Blossom" light theme with saturated pink accents.
 *
 * A playful, feminine light mode. The background is a warm off-white with
 * a faint rose tint. Accents are vivid hot-pink, borders and surfaces stay
 * gentle so the pink doesn't overwhelm. Looks great on any screen.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const blossomPink = {
  id:   'blossomPink',
  name: 'Blossom',
  dark: false,

  bgBase:    '#fdf5f7',  // rose-tinted near-white
  bgSurface: '#ffffff',
  bgCard:    '#fceef2',  // very light blush
  bgRaised:  '#f6e0e8',  // soft pink input background

  accent:     '#e0357a',  // vivid hot-pink
  accentDim:  '#b8195c',  // deeper magenta on hover
  accentGlow: 'rgba(224,53,122,0.18)',
  accentBg:   'rgba(224,53,122,0.08)',

  border:     'rgba(224,53,122,0.18)',
  borderSoft: 'rgba(224,53,122,0.09)',

  text1: '#2a0a14',  // very dark rose-black
  text2: '#6e3348',  // medium rose-brown
  text3: '#b07888',  // muted dusty rose

  shadowCard: '0 2px 16px rgba(224,53,122,0.10)',
  shadowGlow: '0 0 32px rgba(224,53,122,0.12)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
