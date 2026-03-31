/**
 * event.service.js — Event HTTP service.
 *
 * Endpoints (when MOCK_MODE = false):
 *   GET    /events               → CalEvent[]  (with optional query params)
 *   GET    /events/:id           → CalEvent
 *   POST   /events    body       → CalEvent
 *   PUT    /events/:id body      → CalEvent
 *   DELETE /events/:id           → void
 *
 * Query params for GET /events:
 *   calendarId  — filter by calendar
 *   from        — ISO date string, inclusive
 *   to          — ISO date string, inclusive
 */

import { api, MOCK_MODE } from './api.js';
import { sampleEvents } from '../sampleData.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} CalEvent
 * @property {number|string} id
 * @property {string}        title
 * @property {Date}          date      — local Date object (parsed from API)
 * @property {string}        start     — "HH:MM"
 * @property {string}        end       — "HH:MM"
 * @property {string}        calendar  — calendar id
 * @property {string}        category  — category id
 * @property {string}        color     — hex colour
 * @property {string}        location
 * @property {string}        desc
 */

// ─── Serialisation helpers ────────────────────────────────────────────────────

/**
 * Convert an API event (with ISO date string) to a local CalEvent (with Date).
 * @param {Object} raw
 * @returns {CalEvent}
 */
function deserialise(raw) {
  return {
    ...raw,
    date: raw.date instanceof Date ? raw.date : new Date(raw.date),
  };
}

/**
 * Convert a local CalEvent to a plain API payload (Date → ISO string).
 * @param {CalEvent} ev
 * @returns {Object}
 */
function serialise(ev) {
  return {
    ...ev,
    date: ev.date instanceof Date ? ev.date.toISOString().slice(0, 10) : ev.date,
  };
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch events, optionally filtered by calendar and date range.
 *
 * @param {{ calendarId?: string, from?: Date, to?: Date }} [filters]
 * @returns {Promise<CalEvent[]>}
 */
export async function fetchEvents(filters = {}) {
  if (MOCK_MODE) return sampleEvents.map(deserialise);

  const params = new URLSearchParams();
  if (filters.calendarId) params.set('calendarId', filters.calendarId);
  if (filters.from)       params.set('from', filters.from.toISOString().slice(0, 10));
  if (filters.to)         params.set('to',   filters.to.toISOString().slice(0, 10));

  const query = params.toString();
  const data  = await api.get(`/events${query ? `?${query}` : ''}`);
  return data.map(deserialise);
}

/**
 * Fetch a single event by id.
 * @param {string|number} id
 * @returns {Promise<CalEvent>}
 */
export async function fetchEvent(id) {
  if (MOCK_MODE) {
    const ev = sampleEvents.find(e => e.id === id);
    return ev ? deserialise(ev) : null;
  }
  const data = await api.get(`/events/${id}`);
  return deserialise(data);
}

/**
 * Create a new event.
 * @param {Omit<CalEvent, 'id'>} payload
 * @returns {Promise<CalEvent>}
 */
export async function createEvent(payload) {
  if (MOCK_MODE) {
    return deserialise({ id: Date.now(), ...payload });
  }
  const data = await api.post('/events', serialise(payload));
  return deserialise(data);
}

/**
 * Update an existing event.
 * @param {string|number} id
 * @param {Partial<CalEvent>} payload
 * @returns {Promise<CalEvent>}
 */
export async function updateEvent(id, payload) {
  if (MOCK_MODE) return deserialise({ id, ...payload });
  const data = await api.put(`/events/${id}`, serialise(payload));
  return deserialise(data);
}

/**
 * Delete an event.
 * @param {string|number} id
 * @returns {Promise<void>}
 */
export async function deleteEvent(id) {
  if (MOCK_MODE) return;
  return api.delete(`/events/${id}`);
}
