/**
 * sunflower.js — "Sunflower" dark theme with vivid #FFD32C accents.
 *
 * Deep near-black background with warm brown undertones.
 * The accent is a bold sunflower yellow that pops on dark surfaces.
 */
import { FONTS, SIZES, RADII, CAT_COLORS } from './tokens.js';

export const sunflower = {
  id:   'sunflower',
  name: 'Sunflower',
  dark: true,

  bgBase:    '#0f0c05',  // very dark with a warm brown undertone
  bgSurface: '#161108',
  bgCard:    '#1e170b',
  bgRaised:  '#271f0f',

  accent:     '#FFD32C',  // sunflower yellow
  accentDim:  '#bf9e21',  // muted golden
  accentGlow: 'rgba(255,211,44,0.18)',
  accentBg:   'rgba(255,211,44,0.07)',

  border:     'rgba(255,211,44,0.12)',
  borderSoft: 'rgba(255,211,44,0.05)',

  text1: '#f7f1dc',  // warm near-white
  text2: '#b8a878',  // warm mid-tone
  text3: '#6b5d34',  // muted olive-brown

  shadowCard: '0 4px 24px rgba(0,0,0,0.5)',
  shadowGlow: '0 0 48px rgba(255,211,44,0.12)',

  ...FONTS, ...SIZES, ...RADII, ...CAT_COLORS,
};
