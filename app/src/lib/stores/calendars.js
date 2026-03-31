/**
 * stores/calendars.js — Calendar list state and CRUD.
 *
 * Exports the `calendars` store and helpers for loading, creating,
 * updating, deleting, and toggling calendar filter visibility.
 * Does NOT import from other data stores to avoid circular deps.
 */

import { writable, get } from 'svelte/store';
import { sampleCalendars } from '../sampleData.js';
import * as calSvc  from '../services/calendar.service.js';
import { showToast } from './ui.js';

// ── Store ────────────────────────────────────────────────────

/** @type {import('svelte/store').Writable<import('../services/calendar.service').Calendar[]>} */
export const calendars = writable([...sampleCalendars]);

// ── Load ─────────────────────────────────────────────────────

export async function loadCalendars() {
  try {
    const data = await calSvc.fetchCalendars();
    if (data) calendars.set(data.map(c => ({ on: true, ...c })));
  } catch (e) {
    showToast('Could not load calendars: ' + e.message, 'error');
  }
}

// ── Create ───────────────────────────────────────────────────

/**
 * @param {{ name: string, color: string, description?: string }} payload
 */
export async function createCalendar(payload) {
  try {
    const cal = await calSvc.createCalendar(payload);
    calendars.update(list => [...list, { on: true, role: 'admin', ...cal }]);
    showToast(`Calendar "${cal.name}" created`, 'success');
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
 * @returns {string} — the deleted calendar id (for callers to cascade)
 */
export async function removeCalendar(id) {
  const cal = get(calendars).find(c => c.id === id);
  try {
    await calSvc.deleteCalendar(id);
    calendars.update(list => list.filter(c => c.id !== id));
    showToast(`Calendar "${cal?.name}" deleted`);
    return id;
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
    throw e;
  }
}

// ── Filter toggle ─────────────────────────────────────────────

/** Toggle a calendar's visibility in the filter. */
export function toggleCalendar(id) {
  calendars.update(list =>
    list.map(c => c.id === id ? { ...c, on: !c.on } : c)
  );
}
