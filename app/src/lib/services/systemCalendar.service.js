/**
 * systemCalendar.service.js — export an event to the device's own calendar.
 *
 * Opens the system calendar's new-event editor prefilled, via a native
 * ACTION_INSERT intent (see CalendarBridgePlugin.kt). The user picks the
 * target calendar and confirms; nothing is written without them.
 *
 * The event's description carries a `selfcalendar://event?id=...` deep link
 * back to this app, so the copy in their calendar is a pointer rather than a
 * dead end. That link is handled in src/routes/+layout.svelte.
 *
 * Note this is a one-way, one-time *copy*, not a sync. Editing the event
 * here afterwards does not update the copy in the system calendar, and vice
 * versa. A real two-way sync would need a sync adapter (or an ICS
 * subscription feed served by the API) — deliberately out of scope, but the
 * wording in the UI should not imply more than a copy.
 */

import { registerPlugin, Capacitor } from '@capacitor/core';
import { toRRule } from '../rrule.js';
import { APP_NAME } from '../config.js';

const CalendarBridge = registerPlugin('CalendarBridge');

/**
 * Whether exporting is possible: a native platform with a calendar app
 * installed. Web always returns false — the intent has no web equivalent.
 *
 * @returns {Promise<boolean>}
 */
export async function canExportToSystemCalendar() {
  if (!Capacitor.isNativePlatform()) return false;
  try {
    const { available } = await CalendarBridge.isAvailable();
    return available === true;
  } catch {
    return false;
  }
}

/**
 * Build the description written into the system calendar event.
 *
 * The deep link goes on its own last line so it stays tappable in calendar
 * apps that autolink URLs, and after the user's own text so it doesn't
 * bury it.
 *
 * @param {object} ev Internal CalEvent
 * @returns {string}
 */
export function buildDescription(ev) {
  const parts = [];
  if (ev.description?.trim()) parts.push(ev.description.trim());
  if (ev.id != null && ev.id !== -1) {
    parts.push(`Open in ${APP_NAME}: selfcalendar://event?id=${encodeURIComponent(ev.id)}`);
  }
  return parts.join('\n\n');
}

/**
 * Resolve an event's start and end to epoch milliseconds.
 *
 * All-day events are sent as local midnight to local midnight of the day
 * *after* the last day, which is the half-open range CalendarContract
 * expects — passing the last day's own midnight makes a one-day event show
 * as zero-length. Timed events use the stored Dates directly, which already
 * carry the right wall-clock time (serialise/deserialise in
 * event.service.js keep start/end in sync with startDate/endDate).
 *
 * @param {object} ev Internal CalEvent
 * @returns {{startMs: number, endMs: number}}
 */
export function resolveRange(ev) {
  const start = new Date(ev.startDate);
  const end = new Date(ev.endDate ?? ev.startDate);

  if (ev.allDay) {
    start.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);
    if (end.getTime() <= start.getTime()) {
      end.setDate(end.getDate() + 1);
    }
    return { startMs: start.getTime(), endMs: end.getTime() };
  }

  // A zero-length or inverted timed event would open the editor with a
  // nonsensical range; default it to an hour rather than exporting that.
  if (end.getTime() <= start.getTime()) {
    return { startMs: start.getTime(), endMs: start.getTime() + 3600_000 };
  }
  return { startMs: start.getTime(), endMs: end.getTime() };
}

/**
 * Open the system calendar's editor prefilled with this event.
 *
 * Resolves when the editor has been *opened* — there is no callback from
 * the system editor telling us whether the user saved, so this cannot
 * confirm the event was created. Callers should word their feedback
 * accordingly.
 *
 * @param {object} ev Internal CalEvent
 * @returns {Promise<void>}
 * @throws if no calendar app is available or the intent could not be fired
 */
export async function exportToSystemCalendar(ev) {
  if (!Capacitor.isNativePlatform()) {
    throw new Error('Exporting to the device calendar is only available in the app.');
  }

  const { startMs, endMs } = resolveRange(ev);

  await CalendarBridge.createEvent({
    title: ev.title ?? '',
    description: buildDescription(ev),
    location: ev.address ?? '',
    startMs,
    endMs,
    allDay: ev.allDay === true,
    // Recurring events export as a real recurring rule rather than a single
    // occurrence. An unmappable rule yields null, which the native side
    // treats as a one-off — better than exporting a wrong rule.
    rrule: toRRule(ev.recurrence ?? null) ?? '',
  });
}
