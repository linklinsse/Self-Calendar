<script>
  /**
   * CalendarBody.svelte — Dispatches to the correct view component.
   * Uses Svelte's {#if} switching so each view mounts/unmounts cleanly.
   *
   * Fix: re-fetches events whenever the cursor date or active view changes,
   * so navigating to a new week / month / day always loads the right data.
   */

  import { currentView, cursor, loadEvents } from '../../lib/stores/index.js';
  import { weekDays } from '../../lib/utils.js';

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

  // Re-fetch whenever the user navigates to a different date or switches view
  $effect(() => {
    const range = getRange($currentView, $cursor);
    loadEvents(range);
  });
</script>

<main class="cal-body" aria-label="Calendar">
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
  }
</style>
