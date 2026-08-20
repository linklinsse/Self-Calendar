/**
 * rrule.js — convert Self Calendar's internal recurrence shape into an
 * RFC 5545 RRULE string.
 *
 * Android's Calendar provider (and every other calendar app) expects
 * recurrence as an RRULE, so exporting an event needs this direction. The
 * codebase already goes the *other* way — `analyze_recurrence` in
 * api/scripts/import_google_calendar.py parses Google's RRULEs on the way in
 * — and this is deliberately its mirror image: same field mapping, same
 * frequency names, same day abbreviations, so the two can be read side by
 * side when either needs changing.
 *
 * Input is the internal client shape (see event.service.js):
 *   { type: 'daily'|'weekly'|'monthly'|'yearly', interval: number,
 *     days: number[],  ← JS day indices, 0=Sun…6=Sat
 *     endType: 'never'|'count'|'until', count: number, until: 'YYYY-MM-DD' }
 *
 * Deliberately NOT handled, because Self Calendar cannot express them:
 *   - BYMONTHDAY / ordinal BYDAY (e.g. "2nd Monday"). Monthly and yearly
 *     rules here are always anchored to the start date's own day-of-month,
 *     which is RRULE's default when BYMONTHDAY is omitted, so nothing is
 *     lost by leaving it out.
 *   - Multiple rules, RDATE, BYSETPOS, WKST.
 *
 * Note that RFC 5545 monthly/yearly semantics for a day the target month
 * lacks (the 31st, Feb 29) are *skip that month*, which is exactly what
 * _nextOccurrence in utils.js and nextOccurrence in WidgetDataFetcher.kt
 * were both changed to do — so an exported rule recurs on the same days the
 * app itself shows. That alignment is load-bearing; if anyone "fixes"
 * either of those to clamp or roll over instead, exports silently diverge
 * from what the user sees in-app.
 */

const FREQ_BY_TYPE = {
  daily: 'DAILY',
  weekly: 'WEEKLY',
  monthly: 'MONTHLY',
  yearly: 'YEARLY',
};

/** JS day index (0=Sun…6=Sat) → RFC 5545 two-letter day. */
const BYDAY = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];

const pad = n => String(n).padStart(2, '0');

/**
 * Format a Date as an RFC 5545 UTC date-time (the `Z` form).
 *
 * UNTIL is emitted in UTC because RFC 5545 requires it to match DTSTART's
 * form, and a floating local UNTIL is ambiguous for anyone importing the
 * event in another timezone. The internal `until` is a plain 'YYYY-MM-DD'
 * date with no time, so it is treated as the *end* of that day — an event
 * "until the 30th" should include the 30th.
 */
function untilToUtcStamp(untilDate) {
  const d = new Date(untilDate);
  if (Number.isNaN(d.getTime())) return null;
  d.setHours(23, 59, 59, 0);
  return (
    `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}` +
    `T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}Z`
  );
}

/**
 * Build an RFC 5545 RRULE string from an internal recurrence object.
 *
 * @param {object|null} rec Internal recurrence shape, or null.
 * @returns {string|null} e.g. "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE;COUNT=10",
 *                        or null if there is nothing to express.
 */
export function toRRule(rec) {
  if (!rec) return null;

  const freq = FREQ_BY_TYPE[rec.type];
  if (!freq) return null; // unknown type — better to export a one-off than a wrong rule

  const parts = [`FREQ=${freq}`];

  // INTERVAL=1 is the spec default; omitting it keeps the string readable
  // and matches what other calendar apps emit.
  const interval = Math.max(1, Math.trunc(rec.interval || 1));
  if (interval > 1) parts.push(`INTERVAL=${interval}`);

  // BYDAY only means "these weekdays" on a weekly rule. On monthly/yearly it
  // would mean "the Nth weekday of the month", which is not what the app's
  // `days` array represents, so it is only ever emitted for weekly.
  if (rec.type === 'weekly') {
    const days = (rec.days ?? [])
      .filter(d => Number.isInteger(d) && d >= 0 && d <= 6)
      .sort((a, b) => a - b)
      .map(d => BYDAY[d]);
    if (days.length) parts.push(`BYDAY=${days.join(',')}`);
    // No days selected means "the start date's own weekday", which is
    // RRULE's default for FREQ=WEEKLY with no BYDAY — nothing to emit.
  }

  if (rec.endType === 'count') {
    const count = Math.max(1, Math.trunc(rec.count || 1));
    parts.push(`COUNT=${count}`);
  } else if (rec.endType === 'until' && rec.until) {
    const until = untilToUtcStamp(rec.until);
    // A malformed `until` falls through to an unbounded rule rather than
    // emitting a broken UNTIL that other calendar apps may reject outright.
    if (until) parts.push(`UNTIL=${until}`);
  }

  return parts.join(';');
}
