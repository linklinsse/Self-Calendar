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
 * @param {import('./sampleData').CalEvent} ev
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
 * @param {import('./sampleData').CalEvent} ev
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

  for (let iter = 0; iter < SAFETY; iter++) {
    // Check recurrence end conditions BEFORE adding
    if (rec.endType === 'until') {
      const until = rec.until instanceof Date ? rec.until : new Date(rec.until);
      if (midnight(cur) > midnight(until)) break;
    }
    if (rec.endType === 'count' && count >= rec.count) break;
    if (midnight(cur) > rEnd) break; // past range end → stop

    // Does this occurrence overlap [rangeStart, rangeEnd]?
    const occEnd = new Date(cur.getTime() + spanMs);
    if (midnight(occEnd) >= midnight(rangeStart)) {
      results.push(new Date(cur));
    }
    count++;

    // Advance to next occurrence
    const next = _nextOccurrence(cur, rec);
    if (!next) break;
    cur = next;
  }

  return results;
}

/**
 * Expand all events (including recurring) that touch [rangeStart, rangeEnd].
 * Returns a flat array of {ev, startDate, endDate} — one entry per occurrence.
 *
 * @param {import('./sampleData').CalEvent[]} events
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
      const exceptions = new Set((ev.recurrence_exceptions ?? []).map(ex => ex.date));
      const occurrences = getOccurrencesInRange(ev, rangeStart, rangeEnd);
      for (const occStart of occurrences) {
        // Compare by day boundary (midnight unix) to match how exceptions are stored
        const occUnix = Math.floor(midnight(occStart).getTime() / 1000);
        if (exceptions.has(occUnix)) continue;
        const occEnd = new Date(occStart.getTime() + spanMs);
        out.push({ ev, startDate: occStart, endDate: occEnd });
      }
    }
  }

  return out;
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
        const sorted = [...rec.days].sort((a, b) => a - b);
        const curDow = d.getDay();
        const nextDow = sorted.find(day => day > curDow);
        if (nextDow !== undefined) {
          d.setDate(d.getDate() + (nextDow - curDow));
        } else {
          // Jump to next week (×interval), first selected day
          d.setDate(d.getDate() + (7 - curDow + sorted[0]) + (interval - 1) * 7);
        }
        return d;
      }
      // No specific days → advance by N weeks
      d.setDate(d.getDate() + 7 * interval);
      return d;
    }

    case 'monthly':
      d.setMonth(d.getMonth() + interval);
      return d;

    case 'yearly':
      d.setFullYear(d.getFullYear() + interval);
      return d;

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
