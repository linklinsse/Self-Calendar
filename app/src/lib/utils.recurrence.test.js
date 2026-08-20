/**
 * utils.recurrence.test.js — recurrence expansion.
 *
 * `getOccurrencesInRange` is the densest piece of logic in the app and it
 * had no tests, which is how it shipped a cost proportional to the event's
 * *age* rather than to the range being drawn: rendering one month of a daily
 * event started five years ago cost ~1,800 steps to produce ~31 results, and
 * the 1,500-iteration safety cap silently truncated it. A daily event simply
 * stopped rendering once it passed ~4.1 years old, with nothing but a
 * console.warn.
 *
 * The fix (`_fastForwardTo`) skips straight to the requested range. The bulk
 * of this file is therefore a differential test: the fast path is compared
 * against a deliberately naive reference implementation that steps one
 * occurrence at a time with a huge cap, across every combination of rule
 * type, interval, selected weekdays, end condition and event age. The two
 * must agree exactly.
 *
 * That comparison is what caught the first attempt at the weekly fast-path,
 * which assumed the pattern was periodic from the event's start date. It is
 * only periodic from a *selected weekday* — an "every Tuesday" rule starting
 * on a Monday emits that Monday first — so extrapolating from the first
 * irregular cycle doubled the assumed rate and made count-limited series
 * vanish.
 */

import { describe, expect, it } from 'vitest';
import { getOccurrencesInRange } from './utils.js';

const midnight = d => {
  const r = new Date(d);
  r.setHours(0, 0, 0, 0);
  return r;
};

const isoDays = dates => dates.map(d => {
  const m = midnight(d);
  return `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, '0')}-${String(m.getDate()).padStart(2, '0')}`;
});

/**
 * Reference implementation: steps from the event's start with no
 * fast-forwarding and a cap high enough never to bite. Intentionally the
 * slow, obvious version — its only job is to be correct.
 */
function naiveOccurrences(ev, rangeStart, rangeEnd) {
  const rec = ev.recurrence;
  const base = midnight(ev.startDate);
  const spanMs = midnight(ev.endDate) - base;
  const rEnd = midnight(rangeEnd);
  const out = [];
  let cur = new Date(base);
  let count = 0;

  for (let i = 0; i < 500000; i++) {
    if (rec.endType === 'until' && midnight(cur) > midnight(new Date(rec.until))) break;
    if (rec.endType === 'count' && count >= rec.count) break;
    if (midnight(cur) > rEnd) break;

    if (midnight(new Date(cur.getTime() + spanMs)) >= midnight(rangeStart)) {
      out.push(new Date(cur));
    }
    count++;

    const d = new Date(cur);
    const interval = Math.max(1, rec.interval || 1);
    if (rec.type === 'daily') {
      d.setDate(d.getDate() + interval);
    } else if (rec.type === 'weekly') {
      if (rec.days && rec.days.length) {
        // Monday-first, matching RFC 5545's WKST=MO default and the
        // canonical server-side implementation. This reference originally
        // mirrored the implementation's Sunday-first ordering, which meant
        // it agreed with a real bug: an every-other-week Sat+Sun rule split
        // the weekend across the skipped week. The conformance fixture
        // caught it; this reference had to be corrected too, since a
        // differential test is only as good as the thing it differs against.
        const toMondayFirst = jsDay => (jsDay + 6) % 7;
        const sorted = rec.days.map(toMondayFirst).sort((a, b) => a - b);
        const curDow = toMondayFirst(d.getDay());
        const nextDow = sorted.find(x => x > curDow);
        if (nextDow !== undefined) d.setDate(d.getDate() + (nextDow - curDow));
        else d.setDate(d.getDate() + (7 - curDow + sorted[0]) + (interval - 1) * 7);
      } else {
        d.setDate(d.getDate() + 7 * interval);
      }
    } else {
      break; // monthly/yearly are not fast-forwarded, so not compared here
    }
    cur = d;
  }
  return out;
}

const makeEvent = ({ type, interval, days, endType, count, startYear }) => ({
  startDate: new Date(startYear, 0, 7, 9, 0),
  endDate: new Date(startYear, 0, 7, 10, 0),
  recurrence: { type, interval, days, endType, count, until: new Date(2026, 5, 30) },
});

describe('getOccurrencesInRange — fast path matches naive stepping', () => {
  const ranges = [
    ['a month five years in', new Date(2026, 2, 1), new Date(2026, 2, 31)],
    ['the month it starts in', new Date(2019, 0, 1), new Date(2019, 0, 31)],
    ['a three-day window at the start', new Date(2019, 0, 7), new Date(2019, 0, 9)],
    ['a window spanning two months', new Date(2021, 6, 15), new Date(2021, 7, 22)],
    ['a window past every end condition', new Date(2030, 11, 1), new Date(2030, 11, 31)],
  ];

  for (const [rangeLabel, rangeStart, rangeEnd] of ranges) {
    for (const type of ['daily', 'weekly']) {
      for (const interval of [1, 2, 3, 5]) {
        const dayOptions = type === 'weekly' ? [null, [1, 3, 5], [0, 6], [2]] : [null];
        for (const days of dayOptions) {
          for (const endType of ['never', 'count', 'until']) {
            for (const count of [3, 50, 400]) {
              for (const startYear of [2019, 2023, 2026]) {
                const label =
                  `${type} every ${interval}` +
                  `${days ? ` on [${days}]` : ''}` +
                  `, ends ${endType}${endType === 'count' ? `(${count})` : ''}` +
                  `, from ${startYear}, over ${rangeLabel}`;

                it(label, () => {
                  const ev = makeEvent({ type, interval, days, endType, count, startYear });
                  expect(isoDays(getOccurrencesInRange(ev, rangeStart, rangeEnd)))
                    .toEqual(isoDays(naiveOccurrences(ev, rangeStart, rangeEnd)));
                });
              }
            }
          }
        }
      }
    }
  }
});

describe('getOccurrencesInRange — the age regression', () => {
  it('still renders a daily event older than the 1500-iteration safety cap', () => {
    // 1500 daily occurrences is ~4.1 years. Before the fast path this
    // returned nothing at all and only logged a console.warn.
    const ev = {
      startDate: new Date(2010, 0, 1, 9, 0),
      endDate: new Date(2010, 0, 1, 10, 0),
      recurrence: { type: 'daily', interval: 1, days: null, endType: 'never' },
    };
    const occurrences = getOccurrencesInRange(ev, new Date(2026, 2, 1), new Date(2026, 2, 31));
    expect(occurrences).toHaveLength(31);
    expect(isoDays(occurrences)[0]).toBe('2026-03-01');
    expect(isoDays(occurrences).at(-1)).toBe('2026-03-31');
  });

  it('does not warn about truncation for a very old daily event', () => {
    const warnings = [];
    const original = console.warn;
    console.warn = msg => warnings.push(msg);
    try {
      getOccurrencesInRange(
        {
          startDate: new Date(2000, 0, 1),
          endDate: new Date(2000, 0, 1),
          recurrence: { type: 'daily', interval: 1, days: null, endType: 'never' },
        },
        new Date(2026, 2, 1),
        new Date(2026, 2, 31),
      );
    } finally {
      console.warn = original;
    }
    expect(warnings).toEqual([]);
  });

  it('respects a count limit that expires before the requested range', () => {
    const ev = {
      startDate: new Date(2019, 0, 7, 9, 0),
      endDate: new Date(2019, 0, 7, 10, 0),
      recurrence: { type: 'daily', interval: 1, days: null, endType: 'count', count: 10 },
    };
    expect(getOccurrencesInRange(ev, new Date(2026, 2, 1), new Date(2026, 2, 31))).toEqual([]);
  });

  it('emits a weekly rule whose start date is not on a selected weekday', () => {
    // 2019-01-07 is a Monday; the rule selects Tuesdays only. The start date
    // itself is emitted, then the pattern settles at one a week — the case
    // that broke the first attempt at the weekly fast path.
    const ev = {
      startDate: new Date(2019, 0, 7, 9, 0),
      endDate: new Date(2019, 0, 7, 10, 0),
      recurrence: { type: 'weekly', interval: 1, days: [2], endType: 'count', count: 400 },
    };
    const occurrences = isoDays(getOccurrencesInRange(ev, new Date(2026, 2, 1), new Date(2026, 2, 31)));
    expect(occurrences).toEqual([
      '2026-03-03', '2026-03-10', '2026-03-17', '2026-03-24', '2026-03-31',
    ]);
  });
});

describe('getOccurrencesInRange — non-recurring', () => {
  it('returns nothing for an event with no recurrence', () => {
    expect(getOccurrencesInRange(
      { startDate: new Date(2026, 2, 4), endDate: new Date(2026, 2, 4), recurrence: null },
      new Date(2026, 2, 1),
      new Date(2026, 2, 31),
    )).toEqual([]);
  });
});
