/**
 * calendar.service.js — Calendar HTTP service.
 *
 * Endpoints (OpenAPI):
 *   GET    /calendar/                            → Calendar[]
 *   POST   /calendar/              body          → Calendar
 *   GET    /calendar/{id}                        → Calendar
 *   PATCH  /calendar/{id}          body          → Calendar
 *   DELETE /calendar/{id}                        → void
 *
 *   POST   /user_calendar/         body          → UserCalendar
 *   GET    /user_calendar/all/{calendarId}       → UserCalendar[]
 *   GET    /user_calendar/{id}                   → UserCalendar
 *   PATCH  /user_calendar/{id}     body          → UserCalendar
 *   DELETE /user_calendar/{id}                   → void
 */

import { api, MOCK_MODE } from './api.js';
import { sampleCalendars } from '../sampleData.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {'read' | 'write' | 'admin'} CalendarRight
 *
 * @typedef {Object} Calendar
 * @property {string}  id
 * @property {string}  title        — display name (API field, replaces old `name`)
 * @property {string}  [description]
 * @property {string}  [color]      — hex, e.g. "#f4b8c8"
 * @property {boolean} on           — local filter toggle (not persisted)
 *
 * @typedef {Object} UserCalendar
 * @property {string}        id
 * @property {string}        user_id
 * @property {string}        calendar_id
 * @property {CalendarRight} right
 */

// ─── Calendar CRUD ────────────────────────────────────────────────────────────

/**
 * Fetch all calendars the current user has access to.
 * @returns {Promise<Calendar[]>}
 */
export async function fetchCalendars() {
  if (MOCK_MODE) return sampleCalendars.map(c => ({ on: true, ...c }));
  const data = await api.get('/calendar/');
  return data.map(c => ({ on: true, ...c }));
}

/**
 * Create a new calendar.
 * @param {{ title: string, color?: string, description?: string }} payload
 * @returns {Promise<Calendar>}
 */
export async function createCalendar(payload) {
  if (MOCK_MODE) {
    return { id: `cal-${Date.now()}`, on: true, ...payload };
  }
  const cal = await api.post('/calendar/', payload);
  return { on: true, ...cal };
}

/**
 * Fetch a single calendar by id.
 * @param {string} id
 * @returns {Promise<Calendar>}
 */
export async function fetchCalendar(id) {
  if (MOCK_MODE) return sampleCalendars.find(c => c.id === id) ?? null;
  const cal = await api.get(`/calendar/${id}`);
  return { on: true, ...cal };
}

/**
 * Update an existing calendar's metadata.
 * @param {string} id
 * @param {{ title?: string, color?: string, description?: string }} payload
 * @returns {Promise<Calendar>}
 */
export async function updateCalendar(id, payload) {
  if (MOCK_MODE) return { id, ...payload };
  return api.patch(`/calendar/${id}`, payload);
}

/**
 * Delete a calendar.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCalendar(id) {
  if (MOCK_MODE) return;
  return api.delete(`/calendar/${id}`);
}

// ─── User ↔ Calendar links ────────────────────────────────────────────────────

/**
 * Add a user to a calendar with a given right level.
 * @param {{ user_id: string, calendar_id: string, right: CalendarRight }} payload
 * @returns {Promise<UserCalendar>}
 */
export async function addUserCalendar(payload) {
  if (MOCK_MODE) return { id: `lnk-${Date.now()}`, ...payload };
  return api.post('/user_calendar/', payload);
}

/**
 * Fetch all user-calendar links for a given calendar.
 * @param {string} calendarId
 * @returns {Promise<UserCalendar[]>}
 */
export async function fetchUserCalendars(calendarId) {
  if (MOCK_MODE) {
    return [
      { id: 'lnk-1', user_id: 'user-1', calendar_id: calendarId, right: 'O' },
      { id: 'lnk-2', user_id: 'user-2', calendar_id: calendarId, right: 'W' },
    ];
  }
  return api.get(`/user_calendar/all/${calendarId}`);
}

/**
 * Fetch a single user-calendar link by its id.
 * @param {string} lnkId
 * @returns {Promise<UserCalendar>}
 */
export async function fetchUserCalendar(lnkId) {
  if (MOCK_MODE) return null;
  return api.get(`/user_calendar/${lnkId}`);
}

/**
 * Update the right on a user-calendar link.
 * @param {string} lnkId
 * @param {{ right: CalendarRight }} payload
 * @returns {Promise<UserCalendar>}
 */
export async function updateUserCalendar(lnkId, payload) {
  if (MOCK_MODE) return { id: lnkId, ...payload };
  return api.patch(`/user_calendar/${lnkId}`, payload);
}

/**
 * Remove a user-calendar link.
 * @param {string} lnkId
 * @returns {Promise<void>}
 */
export async function deleteUserCalendar(lnkId) {
  if (MOCK_MODE) return;
  return api.delete(`/user_calendar/${lnkId}`);
}
