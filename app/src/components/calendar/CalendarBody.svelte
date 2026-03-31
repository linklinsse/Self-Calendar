<script>
  /**
   * CalendarBody.svelte — Dispatches to the correct view component.
   * Uses Svelte's {#if} switching so each view mounts/unmounts cleanly.
   */

  import { currentView } from '../../lib/stores/index.js';

  import MonthView from './MonthView.svelte';
  import WeekView  from './WeekView.svelte';
  import DayView   from './DayView.svelte';
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
