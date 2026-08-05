/**
 * utils.js — Pure date/time/recurrence helper functions.
 *
 * Imports FIRST_DAY_OF_WEEK and LOCALE from config.js so that week
 * layout and date formatting respect the environment configuration.
 * All other functions are side-effect free and fully testable in isolation.
 */

import { FIRST_DAY_OF_WEEK, LOCALE, HOUR_FORMAT } from './config.js';

// ── Constants ─────────────────────────────────────────────────
export const MONTH_NAMES = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December',
];
export const MONTH_ABBR = [
  'Jan','Feb','Mar','Apr','May','Jun',
  'Jul','Aug','Sep','Oct','Nov','Dec',
];
export const DAY_NAMES = [
  'Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday',
];

// Ordered day abbreviations starting from FIRST_DAY_OF_WEEK.
// e.g. FIRST_DAY_OF_WEEK=1 → ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
//      FIRST_DAY_OF_WEEK=0 → ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
const ALL_DAY_ABBR = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
export const DAY_ABBR_MON = Array.from({ length: 7 }, (_, i) =>
  ALL_DAY_ABBR[(FIRST_DAY_OF_WEEK + i) % 7]
);
export const DOW_LETTERS = Array.from({ length: 7 }, (_, i) =>
  ALL_DAY_ABBR[(FIRST_DAY_OF_WEEK + i) % 7][0]
);

// ── Date normalisation ────────────────────────────────────────

/** Return a new Date at midnight on the same calendar day (no mutation). */
export function midnight(d) {
  const r = new Date(d);
  r.setHours(0, 0, 0, 0);
  return r;
}

/** Number of whole days between two dates (a - b). Negative if b > a. */
export function daysBetween(a, b) {
  return Math.round((midnight(a) - midnight(b)) / 86400000);
}

// ── Date comparisons ──────────────────────────────────────────

export function sameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth()    === b.getMonth()    &&
    a.getDate()     === b.getDate()
  );
}

export function isToday(d) {
  return sameDay(d, new Date());
}

/** True if `date` falls within [startDate, endDate] inclusive (day granularity). */
export function dateInRange(date, startDate, endDate) {
  const d  = midnight(date);
  const s  = midnight(startDate);
  const e  = midnight(endDate);
  return d >= s && d <= e;
}

// ── Event coverage ────────────────────────────────────────────

/**
 * Returns true if the event covers the given calendar day.
 * Handles single-day, multi-day, all-day, and recurring events.
 *
 * @param {import('./services/event.service.js').CalEvent} ev
 * @param {Date} date
 */
export function eventCoversDay(ev, date) {
  const start = ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate);
  const end   = ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate);
  return dateInRange(date, start, end);
}

/** True if the event spans more than one calendar day. */
export function isMultiDay(ev) {
  const s = midnight(ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate));
  const e = midnight(ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate));
  return e > s;
}

// ── Week helpers ──────────────────────────────────────────────

/** First day of the week containing `d`, respecting FIRST_DAY_OF_WEEK config (0=Sun, 1=Mon). */
export function weekStart(d) {
  const dow  = d.getDay();
  const diff = ((dow - FIRST_DAY_OF_WEEK) + 7) % 7;
  const r    = new Date(d);
  r.setDate(d.getDate() - diff);
  r.setHours(0, 0, 0, 0);
  return r;
}

/** Array of 7 Date objects (Mon–Sun) for the week containing `d`. */
export function weekDays(d) {
  const start = weekStart(d);
  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(start);
    day.setDate(start.getDate() + i);
    return day;
  });
}

// ── Month helpers ─────────────────────────────────────────────

export function daysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

/** Full month grid padded to complete rows, respecting FIRST_DAY_OF_WEEK. */
export function buildMonthGrid(year, month) {
  const first    = new Date(year, month, 1);
  const lastDate = daysInMonth(year, month);
  const dow      = first.getDay();
  // How many days from the configured first-day-of-week to the 1st of the month
  const offset   = ((dow - FIRST_DAY_OF_WEEK) + 7) % 7;
  const grid     = [];

  const prevLast = new Date(year, month, 0).getDate();
  for (let i = offset - 1; i >= 0; i--) {
    grid.push(new Date(year, month - 1, prevLast - i));
  }
  for (let d = 1; d <= lastDate; d++) {
    grid.push(new Date(year, month, d));
  }
  const rem = grid.length % 7 === 0 ? 0 : 7 - (grid.length % 7);
  for (let d = 1; d <= rem; d++) {
    grid.push(new Date(year, month + 1, d));
  }
  return grid;
}

// ── Recurrence expansion ──────────────────────────────────────

/**
 * For a recurring event, compute all occurrence start-dates that overlap
 * [rangeStart, rangeEnd]. Returns an array of Date objects.
 *
 * @param {import('./services/event.service.js').CalEvent} ev
 * @param {Date} rangeStart
 * @param {Date} rangeEnd
 * @returns {Date[]}
 */
export function getOccurrencesInRange(ev, rangeStart, rangeEnd) {
  const rec = ev.recurrence;
  if (!rec) return []; // not recurring

  const base    = midnight(ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate));
  const baseEnd = midnight(ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate));
  const spanMs  = baseEnd - base; // duration in ms (may be 0 for single-day)

  const rEnd = midnight(rangeEnd);
  const results = [];
  let cur   = new Date(base);
  let count = 0; // how many we've generated (for endType='count')
  const SAFETY = 1500; // prevent infinite loops

  // Jump straight to the neighbourhood of the requested range rather than
  // stepping there one occurrence at a time from the event's original start.
  //
  // Stepping made the cost proportional to the event's *age*, not to the
  // range being drawn: rendering one month of a daily event started five
  // years ago cost ~1,800 iterations to produce ~31 results, and SAFETY
  // silently truncated at 1,500 — so a daily event simply stopped rendering
  // once it passed ~4.1 years old, with nothing but a console.warn.
  ({ cur, count } = _fastForwardTo(cur, rec, rangeStart, count));

  let truncated = true;
  for (let iter = 0; iter < SAFETY; iter++) {
    // Check recurrence end conditions BEFORE adding
    if (rec.endType === 'until') {
      const until = rec.until instanceof Date ? rec.until : new Date(rec.until);
      if (midnight(cur) > midnight(until)) { truncated = false; break; }
    }
    if (rec.endType === 'count' && count >= rec.count) { truncated = false; break; }
    if (midnight(cur) > rEnd) { truncated = false; break; } // past range end → stop

    // Does this occurrence overlap [rangeStart, rangeEnd]?
    const occEnd = new Date(cur.getTime() + spanMs);
    if (midnight(occEnd) >= midnight(rangeStart)) {
      results.push(new Date(cur));
    }
    count++;

    // Advance to next occurrence
    const next = _nextOccurrence(cur, rec);
    if (!next) { truncated = false; break; }
    cur = next;
  }

  if (truncated) {
    console.warn(
      `getOccurrencesInRange: hit the ${SAFETY}-occurrence safety cap for a ` +
      `recurring event without reaching its end condition or the requested ` +
      `range — results are incomplete.`
    );
  }

  return results;
}

/**
 * Expand all events (including recurring) that touch [rangeStart, rangeEnd].
 * Returns a flat array of {ev, startDate, endDate} — one entry per occurrence.
 *
 * @param {import('./services/event.service.js').CalEvent[]} events
 * @param {Date} rangeStart
 * @param {Date} rangeEnd
 * @returns {Array<{ev: object, startDate: Date, endDate: Date}>}
 */
export function expandEventsForRange(events, rangeStart, rangeEnd) {
  const out = [];

  for (const ev of events) {
    const s = ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate);
    const e = ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate);
    const spanMs = midnight(e) - midnight(s);

    if (!ev.recurrence) {
      // Non-recurring: include if it overlaps the range
      if (midnight(e) >= midnight(rangeStart) && midnight(s) <= midnight(rangeEnd)) {
        out.push({ ev, startDate: new Date(s), endDate: new Date(e) });
      }
    } else {
      // Recurring: expand occurrences within range, skipping exceptions.
      //
      // Compared by calendar *day*, not by exact epoch. Exceptions written
      // by this app are already local midnight (excludeOccurrence sends the
      // occurrence start, and occurrences are local midnight), but the
      // Google importer writes the occurrence's real instant, and the
      // Android widget has always normalised before comparing
      // (WidgetDataFetcher.buildEventsByDate). Requiring an exact match made
      // imported exclusions no-ops on the web app while the widget honoured
      // them — the same database rendering two different calendars.
      const exceptions = new Set(
        (ev.recurrence_exceptions ?? []).map(
          ex => midnight(new Date(ex.date * 1000)).getTime()
        )
      );
      const occurrences = getOccurrencesInRange(ev, rangeStart, rangeEnd);
      for (const occStart of occurrences) {
        if (exceptions.has(midnight(occStart).getTime())) continue;
        const occEnd = new Date(occStart.getTime() + spanMs);
        out.push({ ev, startDate: occStart, endDate: occEnd });
      }
    }
  }

  return out;
}

/**
 * Advance `cur` to the last occurrence at or before `rangeStart`, without
 * visiting every occurrence in between, and return the running occurrence
 * count updated to match.
 *
 * Only 'daily' and 'weekly' are fast-forwarded. They are the rules whose
 * occurrence count grows fast enough to matter — 365 and 52 a year against
 * the 1,500-iteration safety cap, i.e. 4.1 and 28.7 years of headroom.
 * 'monthly' and 'yearly' produce at most 12 and 1 a year, so stepping them
 * is already cheap and left alone rather than reimplemented: their
 * skip-the-month-if-the-anchor-day-does-not-exist semantics (see
 * _nextOccurrence) make the occurrence count non-uniform, and getting that
 * arithmetic subtly wrong would corrupt the count for endType='count'.
 *
 * Never overshoots an endType='count' limit, so the caller's own end-
 * condition checks still decide when the series actually stops.
 *
 * @returns {{cur: Date, count: number}}
 */
function _fastForwardTo(cur, rec, rangeStart, count) {
  const interval = Math.max(1, rec.interval || 1);
  const gapDays  = daysBetween(rangeStart, cur);
  if (gapDays <= 0) return { cur, count }; // already at or past the range

  /** Clamp so a 'count'-terminated series is never skipped past its end. */
  const clamp = steps => {
    if (rec.endType !== 'count') return steps;
    const remaining = (rec.count ?? 0) - count - 1;
    return Math.max(0, Math.min(steps, remaining));
  };

  if (rec.type === 'daily') {
    const steps = clamp(Math.floor(gapDays / interval));
    if (steps <= 0) return { cur, count };
    const next = new Date(cur);
    next.setDate(next.getDate() + steps * interval);
    return { cur: next, count: count + steps };
  }

  if (rec.type === 'weekly') {
    const selected = (rec.days ?? []).length;

    // The pattern is periodic with a period of exactly `cycleDays` — but
    // only once `cur` sits on a selected weekday. The event's own start does
    // not have to: a "every Tuesday" rule whose start date is a Monday emits
    // that Monday, then settles into the weekly pattern. Counting
    // occurrences in that first irregular cycle and extrapolating from it
    // overestimates the rate (2/week instead of 1/week in that example),
    // which overshoots an endType='count' limit and drops the series
    // entirely. Step past the irregular first occurrence first —
    // _nextOccurrence always lands on a selected day when days is non-empty,
    // so this is at most one step.
    if (selected > 0 && !rec.days.includes(cur.getDay())) {
      if (rec.endType === 'count' && count + 1 >= (rec.count ?? 0)) {
        return { cur, count };
      }
      const stepped = _nextOccurrence(cur, rec);
      if (!stepped) return { cur, count };
      cur = stepped;
      count += 1;
    }

    // Every cycle starting from a selected weekday contains exactly one
    // occurrence per selected day (the days before `cur`'s own weekday are
    // picked up from the following cluster, the ones after it from this
    // one), or exactly one when no days are given.
    const perCycle  = selected > 0 ? selected : 1;
    const cycleDays = 7 * interval;
    let cycles = Math.floor(daysBetween(rangeStart, cur) / cycleDays);
    if (cycles <= 0) return { cur, count };

    if (rec.endType === 'count') {
      const remaining = (rec.count ?? 0) - count - 1;
      cycles = Math.max(0, Math.min(cycles, Math.floor(remaining / perCycle)));
      if (cycles <= 0) return { cur, count };
    }

    const next = new Date(cur);
    next.setDate(next.getDate() + cycles * cycleDays);
    return { cur: next, count: count + cycles * perCycle };
  }

  return { cur, count };
}

/** Compute the next start date for a recurring event. Returns null if none. */
function _nextOccurrence(current, rec) {
  const d        = new Date(current);
  const interval = Math.max(1, rec.interval || 1);

  switch (rec.type) {
    case 'daily':
      d.setDate(d.getDate() + interval);
      return d;

    case 'weekly': {
      // If specific days are specified (0=Sun … 6=Sat):
      if (rec.days && rec.days.length > 0) {
        // Ordered Monday-first, not Sunday-first, which is what `getDay()`
        // returns. The week boundary decides which selected days fall inside
        // the same "active" week, so for interval > 1 it changes the result:
        // an every-other-week Sat+Sun rule keeps the weekend together under
        // a Monday-first week, but splits it across the skip under a
        // Sunday-first one.
        //
        // Monday-first is correct here for three independent reasons: it is
        // RFC 5545's default (WKST=MO), which is how every calendar app
        // reads the FREQ=WEEKLY;INTERVAL=2;BYDAY=SA,SU that rrule.js exports
        // — so a Sunday-first week made exported events recur on different
        // days than the app displayed; the app's own FIRST_DAY_OF_WEEK
        // defaults to Monday; and the canonical server-side implementation
        // (api/app/common/utils/recurrence_expansion.py) uses it. Caught by
        // the conformance fixture, which is exactly what it is for.
        const toMondayFirst = jsDay => (jsDay + 6) % 7;

        const sorted = rec.days.map(toMondayFirst).sort((a, b) => a - b);
        const curDow = toMondayFirst(d.getDay());
        const nextDow = sorted.find(day => day > curDow);
        if (nextDow !== undefined) {
          d.setDate(d.getDate() + (nextDow - curDow));
        } else {
          // Jump to next active week (×interval), first selected day
          d.setDate(d.getDate() + (7 - curDow + sorted[0]) + (interval - 1) * 7);
        }
        return d;
      }
      // No specific days → advance by N weeks
      d.setDate(d.getDate() + 7 * interval);
      return d;
    }

    case 'monthly': {
      // RFC 5545 semantics: a rule anchored on a day-of-month that a
      // target month doesn't have (e.g. the 31st) skips that month
      // entirely, rather than rolling over into the next month (what
      // JS Date.setMonth does natively) or clamping to the month's last
      // day. Both would silently drift the anchor day over time.
      const anchorDay = d.getDate();
      let totalMonths = d.getFullYear() * 12 + d.getMonth();
      let y, m;
      do {
        totalMonths += interval;
        y = Math.floor(totalMonths / 12);
        m = ((totalMonths % 12) + 12) % 12;
      } while (daysInMonth(y, m) < anchorDay);
      d.setFullYear(y, m, anchorDay);
      return d;
    }

    case 'yearly': {
      // Same skip semantics as 'monthly', for a Feb 29 anchor landing on
      // a non-leap year.
      const anchorDay = d.getDate();
      const anchorMonth = d.getMonth();
      let y = d.getFullYear();
      do {
        y += interval;
      } while (daysInMonth(y, anchorMonth) < anchorDay);
      d.setFullYear(y, anchorMonth, anchorDay);
      return d;
    }

    default:
      return null;
  }
}

// ── Time helpers ──────────────────────────────────────────────

export function timeToMinutes(t) {
  if (!t) return 0;
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

export function minutesToTime(m) {
  const h  = Math.floor(m / 60);
  const mn = m % 60;
  return `${String(h).padStart(2, '0')}:${String(mn).padStart(2, '0')}`;
}

export function formatTime(t) {
  if (!t) return '';
  const [h, m] = t.split(':').map(Number);
  if (HOUR_FORMAT === '24') return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  const suffix  = h < 12 ? 'AM' : 'PM';
  const display = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${display}:${String(m).padStart(2, '0')} ${suffix}`;
}

export function hourLabel(h) {
  if (h === 0) return '';
  if (HOUR_FORMAT === '24') return `${String(h).padStart(2, '0')}:00`;
  if (h < 12)  return `${h} AM`;
  if (h === 12) return '12 PM';
  return `${h - 12} PM`;
}

// ── ISO week number ───────────────────────────────────────────

/**
 * Returns the ISO 8601 week number for a given date (week starts Monday).
 * @param {Date} date
 * @returns {number}
 */
export function getISOWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = d.getUTCDay() || 7; // Mon=1 … Sun=7
  d.setUTCDate(d.getUTCDate() + 4 - day); // nearest Thursday
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
}

// ── Formatting ────────────────────────────────────────────────

export function parseInputDate(s) {
  if (!s) return new Date();
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function toInputDate(d) {
  if (!d) return '';
  const date = d instanceof Date ? d : new Date(d);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

/** e.g. "Monday, Apr 11" — locale-aware. */
export function formatLongDay(d) {
  return new Intl.DateTimeFormat(LOCALE, { weekday: 'long', month: 'short', day: 'numeric' }).format(d);
}

/** e.g. "Apr 7 – 13" or "Mar 31 – Apr 6" — locale-aware. */
export function formatWeekRange(d) {
  const days = weekDays(d);
  const s = days[0];
  const e = days[6];
  const fmt = new Intl.DateTimeFormat(LOCALE, { month: 'short', day: 'numeric' });
  if (s.getMonth() === e.getMonth()) {
    return `${fmt.format(s).replace(/\s\d+$/, '')} ${s.getDate()} – ${e.getDate()}`;
  }
  return `${fmt.format(s)} – ${fmt.format(e)}`;
}

/**
 * Human-readable summary of a recurrence rule.
 * e.g. "Every day", "Every 2 weeks on Mon, Wed", "Every month"
 */
export function describeRecurrence(rec) {
  if (!rec) return 'Does not repeat';
  const iv = rec.interval || 1;

  let base = '';
  switch (rec.type) {
    case 'daily':   base = iv === 1 ? 'Every day'  : `Every ${iv} days`;   break;
    case 'weekly': {
      const dayLabels = (rec.days || []).map(d => DAY_ABBR_MON[(d + 6) % 7]).join(', ');
      const suffix    = dayLabels ? ` on ${dayLabels}` : '';
      base = iv === 1 ? `Every week${suffix}` : `Every ${iv} weeks${suffix}`;
      break;
    }
    case 'monthly': base = iv === 1 ? 'Every month' : `Every ${iv} months`; break;
    case 'yearly':  base = iv === 1 ? 'Every year'  : `Every ${iv} years`;  break;
    default: base = 'Repeating';
  }

  if (rec.endType === 'count') return `${base}, ${rec.count}×`;
  if (rec.endType === 'until') {
    const until = rec.until instanceof Date ? rec.until : new Date(rec.until);
    return `${base} until ${MONTH_ABBR[until.getMonth()]} ${until.getDate()}`;
  }
  return base;
}

// ── Overlapping event column layout ───────────────────────────

/**
 * Assign column positions to timed occurrences so overlapping events
 * render side-by-side instead of on top of each other.
 *
 * Returns an array of objects: { occ, col, cols, sm, em }
 *   col  — 0-indexed column this event occupies
 *   cols — total columns in this event's overlap cluster
 *   sm   — start in minutes
 *   em   — end in minutes
 *
 * Algorithm: greedy left-to-right column assignment, then a cluster
 * pass to set the total column count per cluster.
 *
 * @param {Array<{ev: object, startDate: Date, endDate: Date}>} occs
 * @returns {Array<{occ: object, col: number, cols: number, sm: number, em: number}>}
 */
export function computeColumns(occs) {
  if (!occs.length) return [];

  const items = occs
    .map(occ => {
      const sm = timeToMinutes(occ.ev.start ?? '00:00');
      const rawEm = timeToMinutes(occ.ev.end ?? '00:01');
      const em = rawEm > sm ? rawEm : sm + 30; // guarantee non-zero duration
      return { occ, sm, em, col: 0, cols: 1 };
    })
    .sort((a, b) => a.sm - b.sm || b.em - a.em);

  // Greedy column assignment: find the first column whose last event ended before this one starts
  const colEnds = []; // colEnds[c] = end-minute of the last event placed in column c
  for (const item of items) {
    const freeCol = colEnds.findIndex(end => end <= item.sm);
    if (freeCol === -1) {
      item.col = colEnds.length;
      colEnds.push(item.em);
    } else {
      item.col = freeCol;
      colEnds[freeCol] = item.em;
    }
  }

  // Cluster pass: group consecutive overlapping events and set total cols
  let i = 0;
  while (i < items.length) {
    let clEnd = items[i].em;
    let j = i;
    while (j < items.length && items[j].sm < clEnd) {
      if (items[j].em > clEnd) clEnd = items[j].em;
      j++;
    }
    const numCols = Math.max(...items.slice(i, j).map(x => x.col)) + 1;
    for (let k = i; k < j; k++) items[k].cols = numCols;
    i = j;
  }

  return items;
}
