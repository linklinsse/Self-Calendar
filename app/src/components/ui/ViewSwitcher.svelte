<script>
  /**
   * ViewSwitcher.svelte — Reusable month/week/day toggle widget.
   *
   * Props:
   *   compact  — boolean, use single-letter labels (M/W/D) for small screens
   *
   * Reads and writes the shared $currentView store.
   */
  import { currentView } from '../../lib/stores/index.js';

  export let compact = false;

  const VIEWS = [
    { id: 'month', label: 'Month', short: 'M' },
    { id: 'week',  label: 'Week',  short: 'W' },
    { id: 'day',   label: 'Day',   short: 'D' },
  ];
</script>

<div class="view-sw" role="group" aria-label="Calendar view">
  {#each VIEWS as v}
    <button
      class="v-btn"
      class:active={$currentView === v.id}
      on:click={() => $currentView = v.id}
      aria-pressed={$currentView === v.id}
      aria-label="{v.label} view"
    >
      {compact ? v.short : v.label}
    </button>
  {/each}
</div>

<style>
  .view-sw {
    display: flex;
    background: var(--bg-raised);
    border-radius: 10px;
    padding: 3px; gap: 2px;
  }

  .v-btn {
    padding: 6px 14px;
    border-radius: 8px;
    font-size: var(--fs-sm, 15px);
    font-weight: 500;
    color: var(--t2);
    transition: all .14s;
    white-space: nowrap;
    min-width: 32px;
    display: flex; align-items: center; justify-content: center;
  }
  .v-btn.active { background: var(--acc-bg); color: var(--acc); }
  .v-btn:hover:not(.active) { color: var(--t1); }
</style>
