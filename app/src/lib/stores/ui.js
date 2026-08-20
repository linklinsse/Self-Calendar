/**
 * stores/ui.js — UI navigation, overlay and toast state.
 *
 * Contains everything that drives the chrome (no data/business logic):
 *   • Which calendar view is active
 *   • Which date the user is looking at (cursor)
 *   • Open/closed state for sidebar, filter drawer, modals, panels
 *   • Toast notification queue
 */

import { writable } from 'svelte/store';

// ── Calendar navigation ───────────────────────────────────────

/**
 * The active view.
 * @type {import('svelte/store').Writable<'month'|'week'|'day'>}
 */
export const currentView = writable('month');

/**
 * Cursor date — the date the calendar is centred on.
 * Always starts on today so the app opens at the right week/month.
 */
export const cursor = writable(new Date());

// ── Drawer / overlay visibility ───────────────────────────────

/** Mobile sidebar drawer open state. */
export const sidebarOpen = writable(false);

/** Mobile filter drawer open state. */
export const filterDrawerOpen = writable(false);

/**
 * Calendar settings modal.
 * null = closed | string = calendar id being edited.
 */
export const calSettingsId = writable(null);

/**
 * Category editor modal.
 * null = closed | -1 = new | string = category id being edited.
 */
export const catEditorId = writable(null);

/**
 * Calendar creator modal open state.
 * false = closed | true = open (create new calendar form).
 */
export const calCreatorOpen = writable(false);

// ── Event panel / modal ───────────────────────────────────────

/**
 * Add/edit panel.
 * null = closed | object with id=-1 = new | object with real id = edit.
 * @type {import('svelte/store').Writable<object|null>}
 */
export const panelEvent = writable(null);

/** Close the add/edit event panel. */
export function closePanel() { panelEvent.set(null); }

/**
 * Event detail modal.
 * null = closed | number = event id to display.
 */
export const modalEventId = writable(null);

/**
 * The specific occurrence date that was clicked to open the modal.
 * Required to target the right occurrence when excluding a recurrence exception.
 * null when the event is non-recurring.
 * @type {import('svelte/store').Writable<Date|null>}
 */
export const modalOccurrenceDate = writable(null);

// ── Toast notifications ───────────────────────────────────────

/**
 * @typedef {{ text: string, type?: 'info'|'success'|'error' }} ToastMsg
 */

/** @type {import('svelte/store').Writable<ToastMsg|null>} */
export const toast = writable(null);

let _toastTimer = null;

/**
 * Show a toast notification for ~3 seconds.
 * @param {string} text
 * @param {'info'|'success'|'error'} [type]
 */
export function showToast(text, type = 'info') {
  clearTimeout(_toastTimer);
  toast.set({ text, type });
  _toastTimer = setTimeout(() => toast.set(null), 3200);
}
