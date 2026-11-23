/**
 * navigation.test.js — period stepping (Topbar ‹ › and mobile swipe).
 *
 * The swipe gesture and the Topbar buttons share navigatePeriod(): swipe
 * left → next month / week / day depending on the active view, swipe
 * right → previous. These pin the gesture classification and the step
 * sizes per view.
 */

import { beforeEach, describe, expect, it } from 'vitest';
import { get } from 'svelte/store';
import { swipeDirection, SWIPE_MIN_DISTANCE } from './utils.js';
import { cursor, currentView, navigatePeriod, shiftCursorDate } from './stores/ui.js';

describe('swipeDirection', () => {
  it('finger moving left means next period', () => {
    expect(swipeDirection(-120, 10)).toBe(1);
  });

  it('finger moving right means previous period', () => {
    expect(swipeDirection(120, -10)).toBe(-1);
  });

  it('ignores short drags and taps', () => {
    expect(swipeDirection(0, 0)).toBe(0);
    expect(swipeDirection(SWIPE_MIN_DISTANCE - 1, 0)).toBe(0);
    expect(swipeDirection(-(SWIPE_MIN_DISTANCE - 1), 0)).toBe(0);
  });

  it('accepts exactly the minimum distance', () => {
    expect(swipeDirection(-SWIPE_MIN_DISTANCE, 0)).toBe(1);
  });

  it('ignores mostly-vertical or diagonal drags', () => {
    expect(swipeDirection(-80, 200)).toBe(0);
    expect(swipeDirection(100, 60)).toBe(0);   // dx < 2·dy
    expect(swipeDirection(100, 50)).toBe(-1);  // dx = 2·dy → still horizontal enough
  });
});

describe('shiftCursorDate', () => {
  it('month steps land on the 1st, even from the 31st', () => {
    expect(shiftCursorDate('month', new Date(2026, 0, 31), 1)).toEqual(new Date(2026, 1, 1));
    expect(shiftCursorDate('month', new Date(2026, 2, 31), -1)).toEqual(new Date(2026, 1, 1));
  });

  it('month steps cross year boundaries', () => {
    expect(shiftCursorDate('month', new Date(2026, 11, 15), 1)).toEqual(new Date(2027, 0, 1));
    expect(shiftCursorDate('month', new Date(2026, 0, 15), -1)).toEqual(new Date(2025, 11, 1));
  });

  it('week steps move 7 days', () => {
    expect(shiftCursorDate('week', new Date(2026, 10, 23), 1)).toEqual(new Date(2026, 10, 30));
    expect(shiftCursorDate('week', new Date(2026, 10, 23), -1)).toEqual(new Date(2026, 10, 16));
  });

  it('day steps move 1 day, across month ends', () => {
    expect(shiftCursorDate('day', new Date(2026, 10, 30), 1)).toEqual(new Date(2026, 11, 1));
    expect(shiftCursorDate('day', new Date(2026, 11, 1), -1)).toEqual(new Date(2026, 10, 30));
  });
});

describe('navigatePeriod', () => {
  beforeEach(() => cursor.set(new Date(2026, 10, 23)));

  it('follows the active view', () => {
    currentView.set('month');
    navigatePeriod(1);
    expect(get(cursor)).toEqual(new Date(2026, 11, 1));

    currentView.set('week');
    navigatePeriod(-1);
    expect(get(cursor)).toEqual(new Date(2026, 10, 24));

    currentView.set('day');
    navigatePeriod(-1);
    expect(get(cursor)).toEqual(new Date(2026, 10, 23));
  });
});
