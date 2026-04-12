/**
 * stores/events.js — Event list state, CRUD, and derived visible events.
 *
 * visibleEvents now filters by:
 *   1. calendar_id  — the event's calendar must be toggled on
 *   2. category_id  — the event's category must be toggled on
 *   3. category's calendar — if the category's calendar is off, hide the event
 */

import { writable, derived, get } from 'svelte/store';
import { sampleEvents }            from '../sampleData.js';
import * as eventSvc               from '../services/event.service.js';
import { showToast, modalEventId, panelEvent } from './ui.js';
import { calendars }               from './calendars.js';
import { categories }              from './categories.js';

// Local-only ID counter for optimistic mock inserts.
// Only used in MOCK_MODE — real API always returns a server-assigned id.
let _nextId = 100;
function nextId() { return ++_nextId; }

// ── Store ─────────────────────────────────────────────────────

/** @type {import('svelte/store').Writable<import('../services/event.service').CalEvent[]>} */
export const events = writable([...sampleEvents]);

// ── Derived: filtered event list ──────────────────────────────

/**
 * Events visible after applying calendar + category filter toggles.
 *
 * An event is visible when ALL of:
 *  - its calendar_id maps to an enabled calendar
 *  - its category_id (if set) maps to an enabled category
 *  - that category's own calendar_id is also enabled
 *    (so hiding a calendar also hides cross-calendar categories)
 *
 * @type {import('svelte/store').Readable<import('../services/event.service').CalEvent[]>}
 */
export const visibleEvents = derived(
  [events, calendars, categories],
  ([$events, $cals, $cats]) => {
    const okCals = new Set($cals.filter(c => c.on).map(c => c.id));
    const okCats = new Set($cats.filter(c => c.on && okCals.has(c.calendar_id)).map(c => c.id));

    return $events.filter(e => {
      if (!okCals.has(e.calendar_id)) return false;
      if (e.category_id && !okCats.has(e.category_id)) return false;
      return true;
    }).map(e => {
      // Always resolve color from the category so the calendar view reflects
      // the category's colour. Fall back to the event's own stored color
      // (manual override) and finally to the default accent.
      const cat = e.category_id ? $cats.find(c => c.id === e.category_id) : null;
      return { ...e, color: cat?.color ?? e.color ?? '#b8c9f4' };
    });
  }
);

// ── Load ──────────────────────────────────────────────────────

/**
 * Load events for all active calendars for a given date window.
 * Falls back to sample data in MOCK_MODE.
 *
 * @param {{ from?: Date, to?: Date }} [range]
 */
export async function loadEvents(range = {}) {
  try {
    const { from, to } = range;
    const calList = get(calendars);

    if (!calList.length) { events.set([]); return; }

    // In MOCK_MODE fetchEvents ignores filters and returns sample data
    const results = await Promise.all(
      calList.map(cal =>
        eventSvc.fetchEvents({ calendarId: cal.id, from, to })
      )
    );

    // Deduplicate by id in case a calendar appears in multiple requests
    const seen = new Set();
    const all  = results.flat().filter(e => {
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    });

    events.set(all);
  } catch (e) {
    showToast('Could not load events: ' + e.message, 'error');
  }
}

// ── Save (create or update) ───────────────────────────────────

/**
 * Persist an event from the EventPanel form data.
 * Accepts both old (calendar/category) and new (calendar_id/category_id) field names.
 *
 * @param {object} formData
 */
export async function saveEvent(formData) {
  const payload = {
    ...formData,
    startDate:   formData.startDate instanceof Date ? formData.startDate : new Date(formData.startDate),
    endDate:     formData.endDate   instanceof Date ? formData.endDate   : new Date(formData.endDate ?? formData.startDate),
  };

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
    panelEvent.set(null);
  } catch (e) {
    showToast('Could not save event: ' + e.message, 'error');
  }
}

// ── Delete ────────────────────────────────────────────────────

/**
 * @param {number|string} id
 */
export async function deleteEvent(id) {
  const ev = get(events).find(e => e.id === id);
  modalEventId.set(null);
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
 * @param {string} calendarId
 */
export function removeEventsByCalendar(calendarId) {
  events.update(list => list.filter(e => e.calendar_id !== calendarId));
}
