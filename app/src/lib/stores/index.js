/**
 * stores/index.js — Public store API. Components import from here only.
 * Compound ops (login, logout, openAddPanel, removeCalendar cascade) live here.
 */
import { get } from 'svelte/store';
import * as authSvc from '../services/auth.service.js';
import * as calSvc  from '../services/calendar.service.js';

export * from './auth.js';
export * from './ui.js';
export * from './calendars.js';
export * from './categories.js';
export * from './events.js';

import { currentUser, authLoading }                               from './auth.js';
import { sidebarOpen, filterDrawerOpen, panelEvent,
         cursor, showToast }                                      from './ui.js';
import { calendars, loadCalendars }                               from './calendars.js';
import { categories, loadCategories,
         removeCategoriesByCalendar }                             from './categories.js';
import { events, loadEvents, removeEventsByCalendar }             from './events.js';
import { removeCalendar as _removeCalBase }                       from './calendars.js';

// ── Auth compound ops ─────────────────────────────────────────

/** Login with username + password, then bootstrap app data. */
export async function loginUser(username, password) {
  authLoading.set(true);
  try {
    const user = await authSvc.login(username, password);
    currentUser.set(user);
    await Promise.all([loadCalendars(), loadCategories()]);
    await loadEvents(); // after calendars are loaded
  } finally { authLoading.set(false); }
}

/** Log out and reset all stores. */
export async function logoutUser() {
  await authSvc.logout().catch(() => {});
  currentUser.set(null);
  events.set([]); calendars.set([]); categories.set([]);
  panelEvent.set(null);
  sidebarOpen.set(false);
  filterDrawerOpen.set(false);
}

// ── Calendar: cascade delete ──────────────────────────────────

/** Delete calendar AND cascade-remove its events and categories. */
export async function removeCalendar(id) {
  await _removeCalBase(id);
  removeEventsByCalendar(id);
  removeCategoriesByCalendar(id);
}

// ── Event panel ───────────────────────────────────────────────

/** Open add panel with defaults for the given date/time. */
export function openAddPanel(date, startTime) {
  const firstCal = get(calendars)[0];
  const firstCat = get(categories).find(c => c.calendar_id === firstCal?.id);
  const base     = date || get(cursor);
  panelEvent.set({
    id: -1, title: '',
    startDate: base, endDate: base, allDay: false,
    start: startTime || '09:00',
    end:   startTime ? _bumpHour(startTime) : '10:00',
    calendar_id: firstCal?.id    || '',
    category_id: firstCat?.id    || '',
    // Legacy aliases so EventPanel doesn't need changes yet
    calendar:    firstCal?.id    || '',
    category:    firstCat?.id    || '',
    color:       firstCat?.color || '#f4b8c8',
    adresse: '', location: '', description: '', desc: '', recurrence_id: null, recurrence: null,
  });
}

/** Open edit panel pre-filled with an existing event. */
export function openEditPanel(id) {
  const ev = get(events).find(e => e.id === id);
  if (!ev) return;
  panelEvent.set({
    ...ev,
    // Ensure both alias sets are present for EventPanel
    calendar_id: ev.calendar_id ?? ev.calendar,
    category_id: ev.category_id ?? ev.category ?? null,
    calendar:    ev.calendar_id ?? ev.calendar,
    category:    ev.category_id ?? ev.category ?? null,
    startDate: ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate ?? ev.date),
    endDate:   ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate   ?? ev.startDate ?? ev.date),
  });
}

/**
 * Open add panel pre-filled with a COPY of an existing event.
 * @param {number|string} id
 */
export function openDuplicatePanel(id) {
  const ev = get(events).find(e => e.id === id);
  if (!ev) return;
  panelEvent.set({
    ...ev,
    id:          -1,
    title:       `Copy of ${ev.title}`,
    calendar_id: ev.calendar_id ?? ev.calendar,
    category_id: ev.category_id ?? ev.category ?? null,
    calendar:    ev.calendar_id ?? ev.calendar,
    category:    ev.category_id ?? ev.category ?? null,
    startDate: ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate ?? ev.date),
    endDate:   ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate   ?? ev.startDate ?? ev.date),
  });
}

// ── User-Calendar member management ──────────────────────────

export async function addCalendarMember(calId, userId, right) {
  const link = await calSvc.addUserCalendar({ user_id: userId, calendar_id: calId, right });
  showToast(`User added with right "${right}"`, 'success');
  return link;
}

export async function changeCalendarMemberRole(lnkId, right) {
  await calSvc.updateUserCalendar(lnkId, { right });
  showToast('Right updated', 'success');
}

export async function removeCalendarMember(lnkId) {
  await calSvc.deleteUserCalendar(lnkId);
  showToast('Member removed');
}

function _bumpHour(t) {
  const [h, m] = t.split(':').map(Number);
  return `${String(Math.min(h+1, 23)).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
}
