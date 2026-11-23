<script>
  /**
   * CalendarBody.svelte — Dispatches to the correct view component.
   * Uses Svelte's {#if} switching so each view mounts/unmounts cleanly.
   *
   * Fix: re-fetches events whenever the cursor date or active view changes,
   * so navigating to a new week / month / day always loads the right data.
   */

  import { currentView, cursor, calendars, loadEvents, navigatePeriod } from '../../lib/stores/index.js';
  import { weekDays, swipeDirection } from '../../lib/utils.js';

  import MonthView from './MonthView.svelte';
  import WeekView  from './WeekView.svelte';
  import DayView   from './DayView.svelte';

  /**
   * Compute the date window to fetch for the current view + cursor.
   * We always fetch a little wider than the visible range so the
   * all-day banner and cross-midnight events are never clipped.
   */
  function getRange(view, cursorDate) {
    const d = new Date(cursorDate);
    if (view === 'week') {
      const days = weekDays(d);
      const from = new Date(days[0]); from.setHours(0, 0, 0, 0);
      const to   = new Date(days[6]); to.setHours(23, 59, 59, 999);
      return { from, to };
    }
    if (view === 'day') {
      const from = new Date(d); from.setHours(0, 0, 0, 0);
      const to   = new Date(d); to.setHours(23, 59, 59, 999);
      return { from, to };
    }
    // month — fetch the whole month (+ 1 week buffer on each side)
    const from = new Date(d.getFullYear(), d.getMonth(), 1);
    from.setDate(from.getDate() - 7);
    const to   = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    to.setDate(to.getDate() + 7);
    return { from, to };
  }

  // Re-fetch whenever the user navigates to a different date/view, or the
  // calendar list itself changes. `$calendars` is read here only to create
  // that reactive dependency — loadEvents() reads the store's value itself.
  // Without it, this effect only tracked $currentView/$cursor: on login,
  // AppShell (and this component) mounts the instant currentUser is set,
  // which happens *before* loginUser()'s loadCalendars() has resolved —
  // this ran once against an empty calendar list and never re-ran once
  // calendars actually loaded, since nothing it depended on changed again.
  $effect(() => {
    const range = getRange($currentView, $cursor);
    void $calendars;
    loadEvents(range);
  });

  // ── Swipe navigation (touch devices) ────────────────────────
  // Swipe left → next month/week/day, swipe right → previous, following the
  // active view — same steps as the Topbar ‹ › buttons. Touch events only,
  // so a desktop mouse drag never navigates. A second finger cancels the
  // gesture so a pinch can't be read as a swipe.
  let touchStart = null;

  function onTouchStart(e) {
    touchStart = e.touches.length === 1
      ? { x: e.touches[0].clientX, y: e.touches[0].clientY }
      : null;
  }

  function onTouchMove(e) {
    if (e.touches.length > 1) touchStart = null;
  }

  function onTouchEnd(e) {
    if (!touchStart) return;
    const t   = e.changedTouches[0];
    const dir = swipeDirection(t.clientX - touchStart.x, t.clientY - touchStart.y);
    touchStart = null;
    if (!dir) return;
    // Swallow the synthetic click some WebViews still emit at the end of
    // a drag, so the swipe doesn't also open the day/event under the finger.
    if (e.cancelable) e.preventDefault();
    navigatePeriod(dir);
  }

  function onTouchCancel() { touchStart = null; }
</script>

<main
  class="cal-body"
  aria-label="Calendar"
  ontouchstart={onTouchStart}
  ontouchmove={onTouchMove}
  ontouchend={onTouchEnd}
  ontouchcancel={onTouchCancel}
>
  {#if $currentView === 'month'}
    <MonthView />
  {:else if $currentView === 'week'}
    <WeekView />
  {:else}
    <DayView />
  {/if}
</main>

<style>
  .cal-body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    /* Horizontal drags belong to the swipe handler, not the browser —
       vertical panning and pinch-zoom keep their native behaviour. */
    touch-action: pan-y pinch-zoom;
  }
</style>
