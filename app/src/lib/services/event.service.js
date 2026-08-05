/**
 * event.service.js — Event HTTP service.
 *
 * Endpoints (OpenAPI):
 *   POST  /event/                                → CalEvent
 *   GET   /event/range
 *         ?calendar_ids=<id>&calendar_ids=<id>...
 *         &from_date=<unix>&to_date=<unix>
 *         [&category_ids=<id>&category_ids=<id>...]  → CalEvent[]
 *   GET   /event/{event_id}                      → CalEvent
 *   PATCH /event/{event_id}   body               → CalEvent
 *   DELETE /event/{event_id}                     → void
 *   DELETE /event/{event_id}/{date}               → void (exclude one recurrence occurrence)
 *
 * API date fields are Unix timestamps (integers).
 * Internally the app keeps Date objects on startDate / endDate
 * and "HH:MM" strings on start / end (for timed events).
 */

import { api } from './api.js';
import { toInputDate, parseInputDate } from '../utils.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} CalEvent  — internal app representation
 * @property {number|string} id
 * @property {string}        title
 * @property {string}        calendar_id   — calendar id (API field)
 * @property {string}        [category_id] — category id (API field)
 * @property {Date}          startDate     — local Date object
 * @property {Date}          endDate       — local Date object
 * @property {boolean}       allDay
 * @property {string}        [start]       — "HH:MM" (timed events only)
 * @property {string}        [end]         — "HH:MM" (timed events only)
 * @property {string}        [adresse]     — location / address (API field)
 * @property {string}        [description]
 * @property {string}        [reminder]
 * @property {Object|null}   [recurrence]  — internal recurrence rule (see below)
 * @property {string|null}   color         — per-event colour override, or
 *   null to inherit the category's colour. Stored on the API as of the
 *   0f0a84349a26 migration. Note this is the *override*: the colour a view
 *   should actually paint is resolved in stores/events.js, which falls back
 *   to the category and then to a default.
 */

// ─── Recurrence conversion helpers ───────────────────────────────────────────
//
// Internal format (used by the form and utils.js):
//   { type: 'daily'|'weekly'|'monthly'|'yearly', interval: number,
//     days: number[],        ← JS day indices 0=Sun…6=Sat
//     endType: 'never'|'count'|'until', count: number, until: 'YYYY-MM-DD' }
//
// API format (obj_recurence):
//   { type: 'D'|'W'|'M'|'Y', interval: number,
//     days: '1111100',        ← 7-char bitmask Mon-first
//     endType: 'N'|'C'|'U',  count: number|null, until: unix|null }

const TYPE_TO_API    = { daily:'D', weekly:'W', monthly:'M', yearly:'Y' };
const TYPE_FROM_API  = { D:'daily', W:'weekly', M:'monthly', Y:'yearly' };
const END_TO_API     = { never:'N', count:'C', until:'U' };
const END_FROM_API   = { N:'never', C:'count', U:'until' };

/**
 * Convert internal recurrence to API obj_recurence shape.
 * @param {Object|null} rec — internal recurrence
 * @returns {Object|null}
 */
function toApiRecurrence(rec) {
  if (!rec) return null;

  // Internal days (0=Sun…6=Sat) → Mon-first bitmask
  // Internal day d maps to bitmask position (d + 6) % 7
  const bits = Array(7).fill('0');
  for (const d of (rec.days ?? [])) bits[(d + 6) % 7] = '1';

  // until: 'YYYY-MM-DD' string → unix timestamp
  let until = null;
  if (rec.endType === 'until' && rec.until) {
    until = Math.floor(parseInputDate(rec.until).getTime() / 1000);
  }

  return {
    type:     TYPE_TO_API[rec.type]    ?? 'D',
    interval: rec.interval ?? 1,
    days:     bits.join(''),
    endType:  END_TO_API[rec.endType]  ?? 'N',
    count:    rec.endType === 'count'  ? (rec.count ?? 1) : null,
    until,
  };
}

/**
 * Convert API obj_recurence to internal recurrence shape.
 * @param {Object|null} apiRec
 * @returns {Object|null}
 */
function fromApiRecurrence(apiRec) {
  if (!apiRec) return null;

  // Mon-first bitmask → internal days array (0=Sun…6=Sat)
  // Bitmask position i maps to internal day (i + 1) % 7
  const days = [];
  if (typeof apiRec.days === 'string') {
    for (let i = 0; i < 7; i++) {
      if (apiRec.days[i] === '1') days.push((i + 1) % 7);
    }
  }

  // until: unix timestamp → 'YYYY-MM-DD' string
  let until = null;
  if (apiRec.until != null) {
    until = toInputDate(new Date(apiRec.until * 1000));
  }

  return {
    type:     TYPE_FROM_API[apiRec.type]    ?? 'daily',
    interval: apiRec.interval ?? 1,
    days,
    endType:  END_FROM_API[apiRec.endType]  ?? 'never',
    count:    apiRec.count ?? 5,
    until,
  };
}

// ─── Serialisation helpers ────────────────────────────────────────────────────

/**
 * Convert a raw API event (unix timestamps) to an internal CalEvent (Date objects).
 * @param {Object} raw
 * @returns {CalEvent}
 */
function deserialise(raw) {
  const { obj_recurence, ...rest } = raw;
  const startDate = new Date(raw.date_start * 1000);
  const endDate   = new Date(raw.date_end   * 1000);

  // Detect all-day: API stores all-day as local-midnight → local-midnight
  // (same day or next). A span that's an exact multiple of 24h isn't
  // sufficient on its own — e.g. a 14:00-to-14:00-next-day timed event, or
  // a zero-duration event at a non-midnight time, would also match. Require
  // the start to actually be local midnight, matching how the app itself
  // encodes all-day events (see serialise() below).
  const diffSeconds = raw.date_end - raw.date_start;
  const allDay = diffSeconds % 86400 === 0 && diffSeconds >= 0 &&
    startDate.getHours() === 0 && startDate.getMinutes() === 0 && startDate.getSeconds() === 0;

  const startHH = String(startDate.getHours()).padStart(2, '0');
  const startMM = String(startDate.getMinutes()).padStart(2, '0');
  const endHH   = String(endDate.getHours()).padStart(2, '0');
  const endMM   = String(endDate.getMinutes()).padStart(2, '0');

  return {
    ...rest,
    startDate,
    endDate,
    allDay,
    start:                 allDay ? null : `${startHH}:${startMM}`,
    end:                   allDay ? null : `${endHH}:${endMM}`,
    // The raw override, null included. Resolving it to a paintable colour
    // is stores/events.js's job — collapsing null to a default here would
    // make "inherit the category" indistinguishable from "the user picked
    // this exact colour", and there would be no way back to inheriting.
    color:                 raw.color ?? null,
    recurrence:            fromApiRecurrence(obj_recurence ?? null),
    recurrence_exceptions: obj_recurence?.obj_exceptions ?? [],
  };
}

/**
 * Convert an internal CalEvent to an API payload (unix timestamps).
 * @param {object} ev
 * @returns {Object}
 */
function serialise(ev) {
  const startDate = ev.startDate instanceof Date ? new Date(ev.startDate) : new Date(ev.startDate);
  const endDate   = ev.endDate   instanceof Date ? new Date(ev.endDate)   : new Date(ev.endDate ?? ev.startDate);

  if (!ev.allDay) {
    const [sh, sm] = (ev.start || '00:00').split(':').map(Number);
    const [eh, em] = (ev.end   || '00:00').split(':').map(Number);
    startDate.setHours(sh, sm, 0, 0);
    endDate.setHours(eh, em, 0, 0);
  } else {
    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(0, 0, 0, 0);
  }

  return {
    calendar_id:   ev.calendar_id,
    title:         ev.title,
    description:   ev.description ?? null,
    date_start:    Math.floor(startDate.getTime() / 1000),
    date_end:      Math.floor(endDate.getTime()   / 1000),
    category_id:   ev.category_id ?? null,
    // null means "inherit from the category" — see the CalEvent typedef.
    color:         ev.color ?? null,
    address:       ev.adresse ?? null,
    reminder:      ev.reminder ?? null,
    obj_recurence: toApiRecurrence(ev.recurrence ?? null),
  };
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch events for a calendar within a date range.
 *
 * @param {{ calendarIds: string[], from: Date, to: Date, categoryIds?: string[] }} filters
 * @returns {Promise<CalEvent[]>}
 */
export async function fetchEvents(filters = {}) {
  // — do NOT pass through deserialise which expects API unix timestamps.
  const { calendarIds, from, to, categoryIds } = filters;
  if (!calendarIds || !from || !to) return [];

  const params = new URLSearchParams({
    from_date: String(Math.floor(from.getTime() / 1000)),
    to_date:   String(Math.floor(to.getTime()   / 1000)),
  });
  for (const cal of calendarIds) {
    params.append('calendar_ids', cal)
  }
  for (const cat of categoryIds ?? []) {
    params.append('category_ids', cat)
  }

  const data = await api.get(`/event/range?${params}`);
  return (data ?? []).map(deserialise);
}

/**
 * Fetch a single event by id.
 * @param {string|number} id
 * @returns {Promise<CalEvent>}
 */
export async function fetchEvent(id) {
  const data = await api.get(`/event/${id}`);
  return deserialise(data);
}

/**
 * Create a new event.
 * @param {object} payload — internal CalEvent shape
 * @returns {Promise<CalEvent>}
 */
export async function createEvent(payload) {
  const data = await api.post('/event/', serialise(payload));
  return deserialise(data);
}

/**
 * Update an existing event.
 * @param {string|number} id
 * @param {object} payload — internal CalEvent shape
 * @returns {Promise<CalEvent>}
 */
export async function updateEvent(id, payload) {
  const data = await api.patch(`/event/${id}`, serialise(payload));
  return deserialise(data);
}

/**
 * Delete an event.
 * @param {string|number} id
 * @returns {Promise<void>}
 */
export async function deleteEvent(id) {
  return api.delete(`/event/${id}`);
}

/**
 * Exclude a single occurrence of a recurring event (adds an exception).
 * @param {string|number} eventId
 * @param {Date} occurrenceDate — the start date of the occurrence to exclude
 * @returns {Promise<void>}
 */
export async function excludeOccurrence(eventId, occurrenceDate) {
  const unixDate = Math.floor(occurrenceDate.getTime() / 1000);
  return api.delete(`/event/${eventId}/${unixDate}`);
}
