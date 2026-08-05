/**
 * utils.conformance.test.js — the JavaScript expansion must agree with the
 * canonical Python one, case for case.
 *
 * Recurrence used to live in three implementations (Python, JavaScript, and
 * a hand-maintained Kotlin port in the Android widget) and drifted twice —
 * once on monthly/yearly rollover semantics, once on whether an exception
 * matches an occurrence by exact epoch or by calendar day. Each time, two
 * surfaces rendered the same database differently and nothing failed.
 *
 * The Kotlin copy is gone: the widget consumes GET /event/range?expand=true
 * and expands nothing itself. The JavaScript copy stays, because the web
 * client re-derives on every filter and view change and refetching each time
 * would be a real regression — but it is no longer free to disagree.
 *
 * The fixture is generated from the Python implementation by
 * api/scripts/generate_conformance_fixture.py. When a recurrence change is
 * intended: change Python, regenerate, then fix JavaScript until this passes
 * again. If regenerating produces no failures here, the change did not do
 * what you thought it did.
 */

import { describe, expect, it } from 'vitest';
import { getOccurrencesInRange } from './utils.js';
import fixture from './__fixtures__/recurrence-conformance.json';

const API_TO_INTERNAL_TYPE = { D: 'daily', W: 'weekly', M: 'monthly', Y: 'yearly' };
const API_TO_INTERNAL_END = { N: 'never', C: 'count', U: 'until' };

/**
 * Monday-first API bitmask -> the JS day indices utils.js expects (0=Sun).
 * Mirrors fromApiRecurrence in services/event.service.js.
 */
function daysFromBitmask(bitmask) {
  if (typeof bitmask !== 'string') return [];
  const days = [];
  for (let i = 0; i < 7; i++) {
    if (bitmask[i] === '1') days.push((i + 1) % 7);
  }
  return days;
}

function toInternalEvent(testCase) {
  const rec = testCase.recurrence;
  return {
    startDate: new Date(testCase.dateStart * 1000),
    endDate: new Date(testCase.dateEnd * 1000),
    recurrence: {
      type: API_TO_INTERNAL_TYPE[rec.type],
      interval: rec.interval,
      days: daysFromBitmask(rec.days),
      endType: API_TO_INTERNAL_END[rec.endType],
      count: rec.count,
      until: rec.until != null ? new Date(rec.until * 1000) : null,
    },
  };
}

describe('recurrence conformance: JavaScript vs the canonical Python', () => {
  it('the fixture is present and non-trivial', () => {
    // A silently empty fixture would make every case below vacuously pass,
    // which is the one way this suite could fail to do its job.
    expect(fixture.cases.length).toBeGreaterThan(1000);
    expect(fixture.cases.some(c => c.expected.length > 0)).toBe(true);
  });

  // The fixture is generated in UTC so it is reproducible anywhere. The JS
  // implementation works in local civil time, so these agree only when the
  // test process is itself on UTC — which is what TZ=UTC in the vitest
  // config guarantees. Assert it rather than producing thousands of
  // confusing failures if that config is ever dropped.
  it('runs in the timezone the fixture was generated in', () => {
    expect(fixture.timezone).toBe('UTC');
    expect(new Date().getTimezoneOffset()).toBe(0);
  });

  for (const testCase of fixture.cases) {
    it(testCase.name, () => {
      const occurrences = getOccurrencesInRange(
        toInternalEvent(testCase),
        new Date(testCase.rangeStart * 1000),
        new Date(testCase.rangeEnd * 1000),
      );
      expect(occurrences.map(d => Math.floor(d.getTime() / 1000)))
        .toEqual(testCase.expected);
    });
  }
});
