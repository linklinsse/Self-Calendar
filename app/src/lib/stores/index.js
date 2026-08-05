/**
 * stores/index.js — Public store API.
 *
 * This is the single import point for all components. Compound operations
 * that span multiple stores (auth bootstrap, calendar cascade delete,
 * event panel open) live here to avoid circular dependencies between the
 * individual store files.
 */
import { get } from 'svelte/store';
import * as authSvc from '../services/auth.service.js';
import * as calSvc  from '../services/calendar.service.js';
import { getToken } from '../services/api.js';
import { syncWidgetAuth } from '../widgetSync.js';

export * from './auth.js';
export * from './ui.js';
export * from './calendars.js';
export * from './categories.js';
export * from './events.js';

import { currentUser, authLoading }                               from './auth.js';
import { sidebarOpen, filterDrawerOpen, panelEvent,
         cursor, showToast }                                      from './ui.js';
import { calendars, loadCalendars,
         removeCalendar as deleteCalendarBase }                   from './calendars.js';
import { categories, loadCategories,
         removeCategoriesByCalendar }                             from './categories.js';
import { events, removeEventsByCalendar }                         from './events.js';

// ── Auth compound ops ─────────────────────────────────────────

/**
 * Called on app mount — restores a previous session from the stored token.
 * If no token exists the user stays on the LoginScreen silently.
 */
export async function restoreSession() {
  if (!getToken()) return;           // nothing stored → stay on login screen
  authLoading.set(true);
  try {
    const user = await authSvc.getMe();
    if (user) {
      currentUser.set(user);
      // Categories are fetched per-calendar, so calendars must load first.
      await loadCalendars();
      await loadCategories();
      // Events are loaded by CalendarBody.$effect on mount — no extra call needed.
    }
  } catch { /* token expired or invalid — remain logged out */ }
  finally { authLoading.set(false); }
}

/** Register a new account, then auto-login and bootstrap app data. */
export async function registerUser(username, password) {
  authLoading.set(true);
  try {
    const user = await authSvc.register(username, password);
    currentUser.set(user);
    // Categories are fetched per-calendar, so calendars must load first.
    await loadCalendars();
    await loadCategories();
    // Events are loaded by CalendarBody.$effect on mount.
  } finally { authLoading.set(false); }
}

/** Login with username + password, then bootstrap app data. */
export async function loginUser(username, password) {
  authLoading.set(true);
  try {
    const user = await authSvc.login(username, password);
    currentUser.set(user);
    // Categories are fetched per-calendar, so calendars must load first.
    await loadCalendars();
    await loadCategories();
    // Events are loaded by CalendarBody.$effect on mount — no extra call needed.
  } finally { authLoading.set(false); }
}

/**
 * Change the signed-in user's password.
 *
 * The API bumps `token_version` on success, which invalidates every token
 * issued before the change — including the one this session is holding. That
 * is deliberate (changing a leaked password has to evict whoever stole it),
 * but it means the current token is dead the moment the request returns, and
 * every subsequent call would 401.
 *
 * So we immediately re-authenticate with the new password to get a fresh
 * token, and re-push it to the widget, which holds its own copy and would
 * otherwise keep 401ing silently until the user next signed in.
 *
 * @param {string} oldPassword
 * @param {string} newPassword
 */
export async function changePassword(oldPassword, newPassword) {
  const user = get(currentUser);
  if (!user) throw new Error('Not signed in.');

  await authSvc.changePasswordRequest(oldPassword, newPassword);

  // From here the old token is already invalid — a failure re-logging in
  // leaves the session unusable, so let it surface rather than swallowing it.
  await authSvc.login(user.username, newPassword);
  await syncWidgetAuth();
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
  await deleteCalendarBase(id);
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
    color:       firstCat?.color || '#f4b8c8',
    adresse: '', description: '', recurrence_id: null, recurrence: null,
  });
}

/** Open edit panel pre-filled with an existing event. */
export function openEditPanel(id) {
  const ev = get(events).find(e => e.id === id);
  if (!ev) return;
  // The picker needs a colour it can paint, but `ev.color` is the raw
  // override and is null whenever the event inherits. Resolve it here to
  // the same precedence the calendar views use (override -> category ->
  // default); EventPanel converts it back to null on save if it still
  // matches the category.
  const cat = ev.category_id
    ? get(categories).find(c => c.id === ev.category_id)
    : null;

  panelEvent.set({
    ...ev,
    calendar_id: ev.calendar_id,
    category_id: ev.category_id ?? null,
    color: ev.color ?? cat?.color ?? '#b8c9f4',
    startDate: ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate),
    endDate:   ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate),
  });
}

/** Open add panel pre-filled with a copy of an existing event. */
export function openDuplicatePanel(id) {
  const ev = get(events).find(e => e.id === id);
  if (!ev) return;
  panelEvent.set({
    ...ev,
    id:          -1,
    title:       `Copy of ${ev.title}`,
    calendar_id: ev.calendar_id,
    category_id: ev.category_id ?? null,
    startDate: ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate),
    endDate:   ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate),
  });
}

// ── User-Calendar member management ──────────────────────────

export async function addCalendarMember(calId, username, right) {
  const link = await calSvc.addUserCalendar({ username, calendar_id: calId, right });
  showToast(`User added with right "${right}"`, 'success');
  return link;
}

export async function changeCalendarMemberRole(lnkId, right) {
  try {
    await calSvc.updateUserCalendar(lnkId, { right });
    showToast('Right updated', 'success');
  } catch (e) {
    showToast('Failed to update right: ' + e.message, 'error');
    throw e;
  }
}

export async function removeCalendarMember(lnkId) {
  try {
    await calSvc.deleteUserCalendar(lnkId);
    showToast('Member removed');
  } catch (e) {
    showToast('Failed to remove member: ' + e.message, 'error');
    throw e;
  }
}

function _bumpHour(t) {
  const [h, m] = t.split(':').map(Number);
  return `${String(Math.min(h+1, 23)).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
}
