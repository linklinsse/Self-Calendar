/**
 * stores/events.js — Event list state, CRUD, and derived visible events.
 *
 * Imports calendars + categories to build the visibleEvents derived store.
 * Dependency direction: events → calendars, categories  (no circular deps).
 */

import { writable, derived, get } from 'svelte/store';
import { sampleEvents }            from '../sampleData.js';
import * as eventSvc               from '../services/event.service.js';
import { showToast, modalEventId, panelEvent } from './ui.js';
import { calendars }               from './calendars.js';
import { categories }              from './categories.js';
import { nextId }                  from '../utils.js';

// ── Store ─────────────────────────────────────────────────────

/** @type {import('svelte/store').Writable<import('../services/event.service').CalEvent[]>} */
export const events = writable([...sampleEvents]);

// ── Derived: filtered event list ──────────────────────────────

/**
 * Events filtered by the active calendar and category toggles.
 * Re-computes automatically whenever events, calendars, or categories change.
 *
 * @type {import('svelte/store').Readable<import('../services/event.service').CalEvent[]>}
 */
export const visibleEvents = derived(
  [events, calendars, categories],
  ([$events, $cals, $cats]) => {
    const okCals = new Set($cals .filter(c => c.on).map(c => c.id));
    const okCats = new Set($cats.filter(c => c.on).map(c => c.id));
    return $events.filter(e =>
      okCals.has(e.calendar) && okCats.has(e.category)
    );
  }
);

// ── Load ──────────────────────────────────────────────────────

export async function loadEvents() {
  try {
    const data = await eventSvc.fetchEvents();
    if (data) events.set(data);
  } catch (e) {
    showToast('Could not load events: ' + e.message, 'error');
  }
}

// ── Save (create or update) ───────────────────────────────────

/**
 * Save an event from the EventPanel form data.
 *
 * Color policy: we trust formData.color entirely.
 * EventPanel already resets it to the category default on category change.
 *
 * @param {object} formData
 */
export async function saveEvent(formData) {
  const payload = { ...formData };

  try {
    if (payload.id === -1) {
      const created = await eventSvc.createEvent(payload);
      const newEv   = created || { ...payload, id: nextId() };
      events.update(list => [...list, newEv]);
      showToast(`"${newEv.title}" added`, 'success');
    } else {
      const updated = await eventSvc.updateEvent(payload.id, payload);
      const newEv   = updated || payload;
      events.update(list => list.map(e => e.id === newEv.id ? newEv : e));
      showToast(`"${newEv.title}" updated`, 'success');
    }
    panelEvent.set(null); // close panel
  } catch (e) {
    showToast('Could not save event: ' + e.message, 'error');
  }
}

// ── Delete ────────────────────────────────────────────────────

/**
 * Delete an event by id.
 * Closes the detail modal first to avoid a flash of stale data.
 * @param {number|string} id
 */
export async function deleteEvent(id) {
  const ev = get(events).find(e => e.id === id);
  modalEventId.set(null); // close modal before removing from list
  try {
    await eventSvc.deleteEvent(id);
    events.update(list => list.filter(e => e.id !== id));
    if (ev) showToast(`"${ev.title}" deleted`);
  } catch (e) {
    showToast('Could not delete event: ' + e.message, 'error');
  }
}

// ── Remove events by calendar (cascade) ───────────────────────

/**
 * Remove all events belonging to a deleted calendar from local state.
 * Called by the index.js removeCalendar wrapper.
 * @param {string} calendarId
 */
export function removeEventsByCalendar(calendarId) {
  events.update(list => list.filter(e => e.calendar !== calendarId));
}
