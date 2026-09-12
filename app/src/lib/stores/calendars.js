/**
 * stores/calendars.js — Calendar list state and CRUD.
 *
 * Uses `title` (not `name`) to match the OpenAPI schema.
 * Exports the `calendars` store and helpers for loading, creating,
 * updating, deleting, and toggling calendar filter visibility.
 */

import { writable, get } from 'svelte/store';
import * as calSvc from '../services/calendar.service.js';
import { showToast } from './ui.js';

// ── Hidden-calendar persistence ─────────────────────────────────
// Stores *hidden* ids rather than visible ones, so a calendar the server
// hands back that this browser has never seen before (newly created, or
// shared by another user) defaults to visible without needing to know
// about it in advance.
//
// Looked up per call rather than cached at module load (unlike the
// otherwise-similar pattern in themes/index.js) so a test can stub
// `localStorage` without needing to re-import this module.
const HIDDEN_STORAGE_KEY = 'sc_hidden_calendars';

function _loadHiddenIds() {
  try {
    if (typeof localStorage === 'undefined') return new Set();
    const raw = localStorage.getItem(HIDDEN_STORAGE_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set(); // corrupt/blocked storage — fall back to "all visible"
  }
}

function _saveHiddenIds(ids) {
  try {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(HIDDEN_STORAGE_KEY, JSON.stringify([...ids]));
  } catch { /* private mode / storage disabled — visibility just won't persist */ }
}

// ── Store ────────────────────────────────────────────────────
/** @type {import('svelte/store').Writable<import('../services/calendar.service').Calendar[]>} */
export const calendars = writable([]);

// ── Load ─────────────────────────────────────────────────────

export async function loadCalendars() {
  try {
    const data = await calSvc.fetchCalendars();
    const hidden = _loadHiddenIds();
    if (data) calendars.set(data.map(c => ({ ...c, on: !hidden.has(c.id) })));
  } catch (e) {
    showToast('Could not load calendars: ' + e.message, 'error');
  }
}

// ── Create ───────────────────────────────────────────────────

/**
 * @param {{ title: string, color: string, description?: string }} payload
 */
export async function createCalendar(payload) {
  try {
    const cal = await calSvc.createCalendar(payload);
    calendars.update(list => [...list, { on: true, ...cal }]);
    showToast(`Calendar "${cal.title}" created`, 'success');
    return cal;
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
    throw e;
  }
}

// ── Update ───────────────────────────────────────────────────

/**
 * @param {string} id
 * @param {object} payload
 */
export async function updateCalendar(id, payload) {
  try {
    const updated = await calSvc.updateCalendar(id, payload);
    calendars.update(list =>
      list.map(c => c.id === id ? { ...c, ...updated } : c)
    );
    showToast('Calendar updated', 'success');
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

// ── Delete ───────────────────────────────────────────────────

/**
 * @param {string} id
 * @returns {Promise<string>} — the deleted calendar id (for callers to cascade)
 */
export async function removeCalendar(id) {
  const cal = get(calendars).find(c => c.id === id);
  try {
    await calSvc.deleteCalendar(id);
    calendars.update(list => list.filter(c => c.id !== id));
    const hidden = _loadHiddenIds();
    if (hidden.delete(id)) _saveHiddenIds(hidden);
    showToast(`Calendar "${cal?.title}" deleted`);
    return id;
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
    throw e;
  }
}

// ── Filter toggle ─────────────────────────────────────────────

/** Toggle a calendar's visibility in the filter, persisting the change so
 * it survives a reload instead of every calendar re-appearing. */
export function toggleCalendar(id) {
  let nowOn = true;
  calendars.update(list =>
    list.map(c => {
      if (c.id !== id) return c;
      nowOn = !c.on;
      return { ...c, on: nowOn };
    })
  );

  const hidden = _loadHiddenIds();
  if (nowOn) hidden.delete(id); else hidden.add(id);
  _saveHiddenIds(hidden);
}

// ── Reorder ──────────────────────────────────────────────────

/**
 * Reorder the calendar list to the given id order (drag-and-drop in
 * CalendarList.svelte). Applied optimistically; a failed save re-fetches
 * the real (server) order rather than leaving the UI showing an order that
 * didn't actually persist.
 * @param {string[]} orderedIds — every calendar id, in the desired order
 */
export async function reorderCalendars(orderedIds) {
  const before = get(calendars);
  const byId = new Map(before.map(c => [c.id, c]));
  calendars.set(orderedIds.map(id => byId.get(id)).filter(Boolean));

  try {
    await calSvc.reorderCalendars(orderedIds);
  } catch (e) {
    showToast('Could not save calendar order: ' + e.message, 'error');
    calendars.set(before);
  }
}
