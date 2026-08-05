/**
 * rrule.test.js
 *
 * The generator is the inverse of `analyze_recurrence` in
 * api/scripts/import_google_calendar.py, so several of these cases are
 * deliberately the same rules that file's own tests parse — a rule that
 * round-trips through both is the strongest signal the two agree.
 */

import { describe, expect, it } from 'vitest';
import { toRRule } from './rrule.js';

const rec = over => ({
  type: 'daily',
  interval: 1,
  days: [],
  endType: 'never',
  count: null,
  until: null,
  ...over,
});

describe('toRRule — frequencies', () => {
  it('maps each type to its RFC 5545 frequency', () => {
    expect(toRRule(rec({ type: 'daily' }))).toBe('FREQ=DAILY');
    expect(toRRule(rec({ type: 'weekly' }))).toBe('FREQ=WEEKLY');
    expect(toRRule(rec({ type: 'monthly' }))).toBe('FREQ=MONTHLY');
    expect(toRRule(rec({ type: 'yearly' }))).toBe('FREQ=YEARLY');
  });

  it('returns null for no recurrence or an unrecognised type', () => {
    expect(toRRule(null)).toBeNull();
    expect(toRRule(rec({ type: 'hourly' }))).toBeNull();
  });
});

describe('toRRule — interval', () => {
  it('omits the spec default of 1', () => {
    expect(toRRule(rec({ interval: 1 }))).toBe('FREQ=DAILY');
  });

  it('emits anything above 1', () => {
    expect(toRRule(rec({ interval: 3 }))).toBe('FREQ=DAILY;INTERVAL=3');
  });

  it('floors a missing or nonsensical interval to 1', () => {
    expect(toRRule(rec({ interval: 0 }))).toBe('FREQ=DAILY');
    expect(toRRule(rec({ interval: undefined }))).toBe('FREQ=DAILY');
    expect(toRRule(rec({ interval: -5 }))).toBe('FREQ=DAILY');
  });
});

describe('toRRule — BYDAY', () => {
  it('emits selected weekdays in calendar order', () => {
    // days are JS indices: 0=Sun…6=Sat
    expect(toRRule(rec({ type: 'weekly', days: [5, 1, 3] })))
      .toBe('FREQ=WEEKLY;BYDAY=MO,WE,FR');
  });

  it('handles the weekend pair', () => {
    expect(toRRule(rec({ type: 'weekly', days: [0, 6] })))
      .toBe('FREQ=WEEKLY;BYDAY=SU,SA');
  });

  it('omits BYDAY when no days are selected', () => {
    // RRULE's own default for FREQ=WEEKLY is DTSTART's weekday, which is
    // exactly what the app means by an empty days array.
    expect(toRRule(rec({ type: 'weekly', days: [] }))).toBe('FREQ=WEEKLY');
  });

  it('never emits BYDAY on non-weekly rules', () => {
    // On a monthly rule BYDAY would mean "the Nth weekday of the month",
    // which is not what `days` represents.
    expect(toRRule(rec({ type: 'monthly', days: [1, 3] }))).toBe('FREQ=MONTHLY');
    expect(toRRule(rec({ type: 'yearly', days: [1] }))).toBe('FREQ=YEARLY');
  });

  it('ignores out-of-range day indices', () => {
    expect(toRRule(rec({ type: 'weekly', days: [1, 9, -2, null] })))
      .toBe('FREQ=WEEKLY;BYDAY=MO');
  });
});

describe('toRRule — end conditions', () => {
  it('emits nothing for an unbounded rule', () => {
    expect(toRRule(rec({ endType: 'never' }))).toBe('FREQ=DAILY');
  });

  it('emits COUNT', () => {
    expect(toRRule(rec({ endType: 'count', count: 10 }))).toBe('FREQ=DAILY;COUNT=10');
  });

  it('floors a nonsensical count to 1 rather than emitting COUNT=0', () => {
    expect(toRRule(rec({ endType: 'count', count: 0 }))).toBe('FREQ=DAILY;COUNT=1');
  });

  it('emits UNTIL as a UTC stamp at the end of the named day', () => {
    // "until the 30th" must include the 30th, so the stamp is that day's
    // 23:59:59 local, converted to UTC.
    const got = toRRule(rec({ endType: 'until', until: '2026-06-30' }));
    expect(got).toMatch(/^FREQ=DAILY;UNTIL=\d{8}T\d{6}Z$/);

    const stamp = got.split('UNTIL=')[1];
    const asDate = new Date(
      `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}` +
      `T${stamp.slice(9, 11)}:${stamp.slice(11, 13)}:${stamp.slice(13, 15)}Z`
    );
    const localEndOfDay = new Date(2026, 5, 30, 23, 59, 59, 0);
    expect(asDate.getTime()).toBe(localEndOfDay.getTime());
  });

  it('falls back to unbounded rather than emitting a broken UNTIL', () => {
    // Other calendar apps reject a malformed UNTIL outright, which would
    // lose the whole event; an unbounded rule at least imports.
    expect(toRRule(rec({ endType: 'until', until: 'not-a-date' }))).toBe('FREQ=DAILY');
    expect(toRRule(rec({ endType: 'until', until: null }))).toBe('FREQ=DAILY');
  });
});

describe('toRRule — combinations round-trip against the importer', () => {
  it.each([
    [{ type: 'weekly', interval: 1, days: [3] }, 'FREQ=WEEKLY;BYDAY=WE'],
    [{ type: 'weekly', interval: 1, days: [1, 3, 5] }, 'FREQ=WEEKLY;BYDAY=MO,WE,FR'],
    [{ type: 'daily', interval: 1, endType: 'count', count: 10 }, 'FREQ=DAILY;COUNT=10'],
    [
      { type: 'weekly', interval: 3, days: [2], endType: 'count', count: 42 },
      'FREQ=WEEKLY;INTERVAL=3;BYDAY=TU;COUNT=42',
    ],
    [{ type: 'monthly', interval: 2 }, 'FREQ=MONTHLY;INTERVAL=2'],
  ])('%o', (over, expected) => {
    expect(toRRule(rec(over))).toBe(expected);
  });
});
