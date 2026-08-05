/**
 * themes.test.js — the theme registry contract.
 *
 * A theme missing a key does not throw. `applyTheme` sets the corresponding
 * CSS variable to `undefined`, browsers ignore that, and the property keeps
 * whatever the *previous* theme set it to. The result is a half-applied
 * palette that looks like a CSS bug rather than a typo in a data file.
 *
 * These tests make that a build failure instead of an hour of bisecting
 * stylesheets, and they run against every theme automatically — so a theme
 * added tomorrow is covered without anyone remembering to add a test.
 */

import { describe, expect, it } from 'vitest';
import { THEMES, THEME_LIST, resolveTheme } from './index.js';

/** Everything applyTheme() reads. Kept in sync with its `map` object. */
const REQUIRED_KEYS = [
  'id', 'name',
  'bgBase', 'bgSurface', 'bgCard', 'bgRaised',
  'accent', 'accentDim', 'accentGlow', 'accentBg',
  'border', 'borderSoft',
  'text1', 'text2', 'text3',
  'shadowCard', 'shadowGlow',
  'catPersonal', 'catWork', 'catHealth', 'catSocial', 'catTravel',
  'fontDisplay', 'fontBody', 'fontMono',
  'fontSizeXs', 'fontSizeSm', 'fontSizeMd', 'fontSizeLg', 'fontSizeXl', 'fontSizeXxl',
  'radiusSm', 'radiusMd', 'radiusLg', 'radiusXl',
];

describe('theme registry', () => {
  it('has themes', () => {
    expect(THEME_LIST.length).toBeGreaterThan(0);
  });

  it('THEMES is derived from THEME_LIST and cannot drift from it', () => {
    expect(Object.keys(THEMES).sort()).toEqual(THEME_LIST.map(t => t.id).sort());
    for (const theme of THEME_LIST) {
      expect(THEMES[theme.id]).toBe(theme);
    }
  });

  it('has no duplicate ids', () => {
    const ids = THEME_LIST.map(t => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('includes at least one light theme, so `dark: false` stays exercised', () => {
    // Native form controls, scrollbars and date pickers switch on
    // colorScheme, which applyTheme derives from this flag. With every
    // theme dark, that path is never run and breaks unnoticed.
    expect(THEME_LIST.some(t => t.dark === false)).toBe(true);
  });
});

describe.each(THEME_LIST.map(t => [t.name, t]))('theme: %s', (_name, theme) => {
  it.each(REQUIRED_KEYS)('defines %s', (key) => {
    expect(theme[key]).toBeDefined();
    expect(theme[key]).not.toBe('');
  });

  it('has an id matching its registry key', () => {
    expect(THEMES[theme.id]).toBe(theme);
  });

  it('uses valid CSS colour values for the solid palette entries', () => {
    // Only the opaque ones: glow/bg/border entries are deliberately rgba().
    for (const key of ['bgBase', 'bgSurface', 'bgCard', 'bgRaised',
                       'accent', 'accentDim', 'text1', 'text2', 'text3']) {
      expect(theme[key], `${theme.id}.${key}`).toMatch(/^#[0-9a-fA-F]{3,8}$/);
    }
  });
});

describe('resolveTheme', () => {
  it('resolves a known id', () => {
    expect(resolveTheme('unicorn').id).toBe('unicorn');
  });

  it('falls back rather than returning undefined for an unknown id', () => {
    // A stale id in localStorage from a removed theme must not brick the
    // app on next load.
    expect(resolveTheme('no-such-theme')).toBeDefined();
    expect(resolveTheme('no-such-theme').id).toBeTruthy();
  });

  it('falls back for undefined', () => {
    expect(resolveTheme(undefined)).toBeDefined();
  });
});
