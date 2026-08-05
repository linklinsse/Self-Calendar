<script>
  /**
   * FilterDrawer.svelte — Mobile filter overlay.
   *
   * Categories section shows only categories whose calendar is toggled ON.
   * Uses `visibleCategories` derived store (filters by active calendar_ids).
   */

  import { fly, fade } from 'svelte/transition';
  import {
    filterDrawerOpen, calendars, visibleCategories,
    toggleCalendar, toggleCategory,
  } from '../../lib/stores/index.js';
</script>

{#if $filterDrawerOpen}

  <!-- Backdrop -->
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="backdrop"
    onclick={() => $filterDrawerOpen = false}
    in:fade={{ duration: 180 }}
    out:fade={{ duration: 180 }}
    aria-hidden="true"
  ></div>

  <!-- Drawer -->
  <div
    class="drawer"
    role="dialog" aria-modal="true" aria-label="Filters"
    in:fly={{ x: -300, duration: 300, easing: t => 1 - Math.pow(1-t,3) }}
    out:fly={{ x: -300, duration: 240 }}
  >
    <div class="hdr">
      <h2 class="ttl">Filters</h2>
      <button
        class="close"
        onclick={() => $filterDrawerOpen = false}
        aria-label="Close filters"
      >✕</button>
    </div>

    <!-- Calendars -->
    <section class="section">
      <h3 class="sec-title">Calendars</h3>
      {#each $calendars as cal (cal.id)}
        <button
          class="row"
          onclick={() => toggleCalendar(cal.id)}
          aria-pressed={cal.on}
        >
          <span class="dot" style="background:{cal.color}"></span>
          <span class="lbl">{cal.title}</span>
          <span class="chk" class:on={cal.on}>{cal.on ? '✓' : ''}</span>
        </button>
      {/each}
    </section>

    <!-- Categories — only for active calendars -->
    <section class="section">
      <h3 class="sec-title">Categories</h3>
      {#each $visibleCategories as cat (cat.id)}
        <button
          class="row cat-row"
          class:off={!cat.on}
          onclick={() => toggleCategory(cat.id)}
          aria-pressed={cat.on}
        >
          <span class="icon">{cat.icon}</span>
          <span class="lbl">{cat.label}</span>
          <span class="pip" style="background:{cat.color}" class:pip-off={!cat.on}></span>
        </button>
      {/each}
      {#if $visibleCategories.length === 0}
        <p class="empty-hint">Enable a calendar to see its categories.</p>
      {/if}
    </section>
  </div>

{/if}

<style>
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.55); backdrop-filter: blur(3px);
    z-index: 29;
  }

  .drawer {
    position: fixed; top: 0; left: 0; bottom: 0;
    width: min(300px, 88vw);
    background: var(--bg-surf);
    border-right: 1px solid var(--bdr);
    z-index: 30;
    padding: 24px 16px;
    display: flex; flex-direction: column;
    overflow-y: auto;
    box-shadow: 6px 0 32px rgba(0,0,0,.4);
    padding-bottom: calc(66px + 16px);
  }

  .hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 24px;
  }
  .ttl {
    font-family: var(--f-display);
    font-size: var(--fs-xl, 24px); font-weight: 400;
  }
  .close {
    width: 30px; height: 30px; border-radius: var(--r-s);
    color: var(--t3); font-size: var(--fs-sm, 15px);
    display: flex; align-items: center; justify-content: center;
    transition: color .15s, background .15s;
  }
  .close:hover { color: var(--acc); background: var(--acc-bg); }

  .section { margin-bottom: 20px; }
  .sec-title {
    font-size: var(--fs-xs, 13px); font-weight: 500; color: var(--t3);
    text-transform: uppercase; letter-spacing: .10em; margin-bottom: 8px;
  }

  .row {
    display: flex; align-items: center; gap: 10px;
    width: 100%; padding: 7px 8px; border-radius: var(--r-s);
    transition: background .13s;
  }
  .row:hover { background: var(--acc-bg); }

  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .lbl { font-size: var(--fs-sm, 15px); color: var(--t2); flex: 1; }

  .chk {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1.5px solid var(--bdr);
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 700; flex-shrink: 0;
    transition: background .13s, border-color .13s;
  }
  .chk.on { background: var(--acc); border-color: var(--acc); color: #1a0812; }

  .cat-row { border-radius: 20px; }
  .cat-row.off .lbl { color: var(--t3); }
  .icon { font-size: var(--fs-sm, 15px); }

  .pip { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; transition: opacity .13s; }
  .pip-off { opacity: .2; }

  .empty-hint {
    font-size: var(--fs-xs, 13px); color: var(--t3);
    padding: 4px 8px; font-style: italic;
  }
</style>
