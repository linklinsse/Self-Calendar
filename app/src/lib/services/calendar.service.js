/**
 * calendar.service.js — Calendar HTTP service.
 *
 * Endpoints (when MOCK_MODE = false):
 *   GET    /calendars                           → Calendar[]
 *   POST   /calendars              body         → Calendar
 *   PUT    /calendars/:id          body         → Calendar
 *   DELETE /calendars/:id                       → void
 *
 *   GET    /calendars/:id/params                → CalendarParams
 *   PUT    /calendars/:id/params   body         → CalendarParams
 *
 *   GET    /calendars/:id/members               → Member[]
 *   POST   /calendars/:id/members  body         → Member
 *   PUT    /calendars/:id/members/:userId body  → Member
 *   DELETE /calendars/:id/members/:userId       → void
 */

import { api, MOCK_MODE } from './api.js';
import { sampleCalendars } from '../sampleData.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {'read' | 'write' | 'admin'} CalendarRole
 *
 * Roles:
 *   read   — can view events
 *   write  — can view + create/edit/delete events
 *   admin  — write + manage members + edit calendar settings
 */

/**
 * @typedef {Object} Calendar
 * @property {string}       id
 * @property {string}       name
 * @property {string}       color        — hex or CSS var
 * @property {boolean}      on           — local filter toggle (not persisted)
 * @property {CalendarRole} role         — current user's role on this calendar
 * @property {string}       [description]
 * @property {string}       ownerId
 */

/**
 * @typedef {Object} CalendarParams
 * @property {string}  calendarId
 * @property {string}  timezone       — IANA tz name, e.g. "Europe/Paris"
 * @property {boolean} showWeekends
 * @property {number}  firstDayOfWeek — 0=Sun, 1=Mon
 * @property {string}  [defaultView]  — 'month'|'week'|'day'
 */

/**
 * @typedef {Object} Member
 * @property {string}       userId
 * @property {string}       name
 * @property {string}       email
 * @property {CalendarRole} role
 * @property {string}       [avatar]
 */

// ─── Calendar CRUD ───────────────────────────────────────────────────────────

/**
 * Fetch all calendars the current user has access to.
 * @returns {Promise<Calendar[]>}
 */
export async function fetchCalendars() {
  if (MOCK_MODE) return sampleCalendars.map(c => ({ ...c, role: 'admin' }));
  const data = await api.get('/calendars');
  // Ensure the `on` filter flag is always present
  return data.map(c => ({ on: true, ...c }));
}

/**
 * Create a new calendar.
 * @param {{ name: string, color: string, description?: string }} payload
 * @returns {Promise<Calendar>}
 */
export async function createCalendar(payload) {
  if (MOCK_MODE) {
    return { id: `cal-${Date.now()}`, on: true, role: 'admin', ...payload };
  }
  const cal = await api.post('/calendars', payload);
  return { on: true, ...cal };
}

/**
 * Update an existing calendar's metadata.
 * @param {string} id
 * @param {{ name?: string, color?: string, description?: string }} payload
 * @returns {Promise<Calendar>}
 */
export async function updateCalendar(id, payload) {
  if (MOCK_MODE) return { id, ...payload };
  return api.put(`/calendars/${id}`, payload);
}

/**
 * Delete a calendar (admin only).
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCalendar(id) {
  if (MOCK_MODE) return;
  return api.delete(`/calendars/${id}`);
}

// ─── Calendar params ──────────────────────────────────────────────────────────

/**
 * Fetch display/behaviour settings for a specific calendar.
 * @param {string} calendarId
 * @returns {Promise<CalendarParams>}
 */
export async function fetchCalendarParams(calendarId) {
  if (MOCK_MODE) {
    return {
      calendarId,
      timezone:       'Europe/Paris',
      showWeekends:   true,
      firstDayOfWeek: 1,
      defaultView:    'month',
    };
  }
  return api.get(`/calendars/${calendarId}/params`);
}

/**
 * Update a calendar's display settings (admin only).
 * @param {string} calendarId
 * @param {Partial<CalendarParams>} payload
 * @returns {Promise<CalendarParams>}
 */
export async function updateCalendarParams(calendarId, payload) {
  if (MOCK_MODE) return { calendarId, ...payload };
  return api.put(`/calendars/${calendarId}/params`, payload);
}

// ─── Calendar members ─────────────────────────────────────────────────────────

/**
 * Fetch all members of a calendar.
 * @param {string} calendarId
 * @returns {Promise<Member[]>}
 */
export async function fetchMembers(calendarId) {
  if (MOCK_MODE) {
    return [
      { userId: 'user-1', name: 'Élise Moreau',  username: 'elise.moreau',   email: 'demo@selfcalendar.app', role: 'admin' },
      { userId: 'user-2', name: 'Thomas Dupont',  username: 'thomas.dupont',  email: 'thomas@example.com',   role: 'write' },
      { userId: 'user-3', name: 'Sophie Martin',  username: 'sophie.martin',  email: 'sophie@example.com',   role: 'read'  },
    ];
  }
  return api.get(`/calendars/${calendarId}/members`);
}

/**
 * Invite a user to a calendar.
 * @param {string}       calendarId
 * @param {string}       email
 * @param {CalendarRole} role
 * @returns {Promise<Member>}
 */
export async function addMember(calendarId, email, role) {
  if (MOCK_MODE) {
    const prefix = email.split('@')[0];
    return { userId: `user-${Date.now()}`, name: prefix, username: prefix, email, role };
  }
  return api.post(`/calendars/${calendarId}/members`, { email, role });
}

/**
 * Change a member's role on a calendar (admin only).
 * @param {string}       calendarId
 * @param {string}       userId
 * @param {CalendarRole} role
 * @returns {Promise<Member>}
 */
export async function updateMemberRole(calendarId, userId, role) {
  if (MOCK_MODE) return { userId, role };
  return api.put(`/calendars/${calendarId}/members/${userId}`, { role });
}

/**
 * Remove a member from a calendar (admin only).
 * @param {string} calendarId
 * @param {string} userId
 * @returns {Promise<void>}
 */
export async function removeMember(calendarId, userId) {
  if (MOCK_MODE) return;
  return api.delete(`/calendars/${calendarId}/members/${userId}`);
}
