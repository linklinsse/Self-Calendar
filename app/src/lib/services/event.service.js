/**
 * event.service.js — Event HTTP service.
 *
 * Endpoints (OpenAPI):
 *   POST  /event/                                → CalEvent
 *   GET   /event/range/{calendar_id}
 *         ?from_date=<unix>&to_date=<unix>
 *         [&category_id=<id>]                   → CalEvent[]
 *   GET   /event/{event_id}                      → CalEvent
 *   PATCH /event/{event_id}   body               → CalEvent
 *   DELETE /event/{event_id}                     → void
 *
 * API date fields are Unix timestamps (integers).
 * Internally the app keeps Date objects on startDate / endDate
 * and "HH:MM" strings on start / end (for timed events).
 */

import { MOCK_MODE } from '../config.js';
import { api } from './api.js';
import { sampleEvents } from '../sampleData.js';
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
 * @property {string}        color         — derived from category, not stored in API
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

  // Detect all-day: API stores all-day as midnight → midnight (same day or next)
  const diffMs = raw.date_end - raw.date_start;
  const allDay = diffMs % 86400 === 0 && diffMs >= 0;

  const startHH = String(startDate.getHours()).padStart(2, '0');
  const startMM = String(startDate.getMinutes()).padStart(2, '0');
  const endHH   = String(endDate.getHours()).padStart(2, '0');
  const endMM   = String(endDate.getMinutes()).padStart(2, '0');

  return {
    ...rest,
    startDate,
    endDate,
    allDay,
    start:      allDay ? null : `${startHH}:${startMM}`,
    end:        allDay ? null : `${endHH}:${endMM}`,
    color:      raw.color ?? '#b8c9f4',
    recurrence: fromApiRecurrence(obj_recurence ?? null),
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
    address:       ev.adresse ?? null,
    reminder:      ev.reminder ?? null,
    obj_recurence: toApiRecurrence(ev.recurrence ?? null),
  };
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch events for a calendar within a date range.
 * In MOCK_MODE returns all sample events regardless of filters.
 *
 * @param {{ calendarId: string, from: Date, to: Date, categoryId?: string }} filters
 * @returns {Promise<CalEvent[]>}
 */
export async function fetchEvents(filters = {}) {
  // sampleEvents already use the internal format (Date objects, start/end strings)
  // — do NOT pass through deserialise which expects API unix timestamps.
  if (MOCK_MODE) return [...sampleEvents];

  const { calendarId, from, to, categoryId } = filters;
  if (!calendarId || !from || !to) return [];

  const params = new URLSearchParams({
    from_date: String(Math.floor(from.getTime() / 1000)),
    to_date:   String(Math.floor(to.getTime()   / 1000)),
  });
  if (categoryId) params.set('category_id', categoryId);

  const data = await api.get(`/event/range/${calendarId}?${params}`);
  return (data ?? []).map(deserialise);
}

/**
 * Fetch a single event by id.
 * @param {string|number} id
 * @returns {Promise<CalEvent>}
 */
export async function fetchEvent(id) {
  if (MOCK_MODE) {
    return sampleEvents.find(e => e.id === id) ?? null;
  }
  const data = await api.get(`/event/${id}`);
  return deserialise(data);
}

/**
 * Create a new event.
 * @param {object} payload — internal CalEvent shape
 * @returns {Promise<CalEvent>}
 */
export async function createEvent(payload) {
  if (MOCK_MODE) {
    return deserialise({ id: Date.now(), ...serialise(payload),
      date_start: Math.floor((payload.startDate ?? new Date()).getTime() / 1000),
      date_end:   Math.floor((payload.endDate   ?? new Date()).getTime() / 1000) });
  }  const data = await api.post('/event/', serialise(payload));
  return deserialise(data);
}

/**
 * Update an existing event.
 * @param {string|number} id
 * @param {object} payload — internal CalEvent shape
 * @returns {Promise<CalEvent>}
 */
export async function updateEvent(id, payload) {
  if (MOCK_MODE) return deserialise({ ...serialise(payload), id });
  const data = await api.patch(`/event/${id}`, serialise(payload));
  return deserialise(data);
}

/**
 * Delete an event.
 * @param {string|number} id
 * @returns {Promise<void>}
 */
export async function deleteEvent(id) {
  if (MOCK_MODE) return;
  return api.delete(`/event/${id}`);
}
