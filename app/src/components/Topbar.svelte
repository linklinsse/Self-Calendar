<script>
  /**
   * Topbar.svelte — App header bar.
   *
   * Uses ViewSwitcher widget (shared with BottomNav).
   * Desktop: hamburger | period | prev/next | Today | ─── | ViewSwitcher | + New
   * Mobile:  hamburger | period(flex:1 centered) | prev/next | Today
   */

  import ViewSwitcher from './ui/ViewSwitcher.svelte';
  import {
    currentView, cursor, sidebarOpen, openAddPanel,
  } from '../lib/stores/index.js';
  import { MONTH_NAMES, MONTH_ABBR, DAY_NAMES, formatWeekRange } from '../lib/utils.js';

  let label = $derived(getLabel($currentView, $cursor));
  let year  = $derived($currentView === 'month' ? ' ' + $cursor.getFullYear() : '');

  function getLabel(view, d) {
    if (view === 'month') return MONTH_NAMES[d.getMonth()];
    if (view === 'week')  return formatWeekRange(d);
    return `${DAY_NAMES[d.getDay()]}, ${MONTH_ABBR[d.getMonth()]} ${d.getDate()}`;
  }

  function navPrev() {
    cursor.update(d => {
      if ($currentView === 'month') return new Date(d.getFullYear(), d.getMonth() - 1, 1);
      if ($currentView === 'week')  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - 7);
      return new Date(d.getFullYear(), d.getMonth(), d.getDate() - 1);
    });
  }
  function navNext() {
    cursor.update(d => {
      if ($currentView === 'month') return new Date(d.getFullYear(), d.getMonth() + 1, 1);
      if ($currentView === 'week')  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 7);
      return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
    });
  }
  function goToday() { cursor.set(new Date()); }
</script>

<header class="topbar">

  <!-- Sidebar toggle (works on both mobile and desktop) -->
  <button class="icon-btn" onclick={() => $sidebarOpen = !$sidebarOpen} aria-label="Toggle sidebar">
    <svg width="17" height="13" viewBox="0 0 17 13" fill="none" aria-hidden="true">
      <rect y="0"  width="17" height="2" rx="1" fill="currentColor"/>
      <rect y="5.5" width="13" height="2" rx="1" fill="currentColor"/>
      <rect y="11" width="17" height="2" rx="1" fill="currentColor"/>
    </svg>
  </button>

  <!-- Period label -->
  <div class="period" aria-live="polite" aria-atomic="true">
    <span class="period-main">{label}</span>{#if year}<span class="period-year">{year}</span>{/if}
  </div>

  <!-- Prev / Next -->
  <nav class="nav-cluster" aria-label="Calendar navigation">
    <button class="nav-btn" onclick={navPrev} aria-label="Previous">‹</button>
    <button class="nav-btn" onclick={navNext} aria-label="Next">›</button>
  </nav>

  <!-- Today (desktop + mobile) -->
  <button class="today-btn" onclick={goToday}>Today</button>

  <div class="spacer"></div>

  <!-- ViewSwitcher widget (desktop only) -->
  <div class="desktop-only">
    <ViewSwitcher />
  </div>

  <!-- New event button (desktop only) -->
  <button class="add-btn desktop-only" onclick={() => openAddPanel()} aria-label="New event">
    <span aria-hidden="true">＋</span> New event
  </button>



</header>

<style>
  .topbar {
    height: 62px; flex-shrink: 0;
    display: flex; align-items: center; gap: 8px;
    padding: 0 18px;
    background: var(--bg-surf);
    border-bottom: 1px solid var(--bdr-soft);
  }

  /* ── Icon button ────────────────────────────────────────── */
  .icon-btn {
    width: 36px; height: 36px; border-radius: var(--r-s);
    color: var(--t2);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: color .16s, background .16s;
  }
  .icon-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Period label ───────────────────────────────────────── */
  .period { display: flex; align-items: baseline; flex-shrink: 0; }
  .period-main {
    font-family: var(--f-display);
    font-size: var(--fs-xl, 24px);
    font-weight: 300; letter-spacing: .02em; white-space: nowrap;
    min-width: 130px;   /* reserve space for longest month "September" */
  }
  .period-year {
    font-family: var(--f-display);
    font-size: var(--fs-lg, 19px);
    color: var(--t3);
  }

  /* ── Prev / Next ────────────────────────────────────────── */
  .nav-cluster { display: flex; gap: 2px; }
  .nav-btn {
    width: 30px; height: 30px; border-radius: 7px;
    border: 1px solid var(--bdr); color: var(--t2);
    font-size: 18px; line-height: 1;
    display: flex; align-items: center; justify-content: center;
    transition: all .15s;
  }
  .nav-btn:hover { color: var(--acc); border-color: var(--acc-dim); background: var(--acc-bg); }

  /* ── Today ──────────────────────────────────────────────── */
  .today-btn {
    padding: 7px 16px; border-radius: 20px;
    border: 1px solid var(--bdr); color: var(--t2);
    font-size: var(--fs-sm, 15px);
    white-space: nowrap; transition: all .15s;
  }
  .today-btn:hover { color: var(--acc); border-color: var(--acc-dim); background: var(--acc-bg); }

  .spacer { flex: 1; min-width: 4px; }

  /* ── Add event ──────────────────────────────────────────── */
  .add-btn {
    display: flex; align-items: center; gap: 7px;
    padding: 9px 20px; border-radius: 20px;
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-size: var(--fs-sm, 15px); font-weight: 600;
    letter-spacing: .03em; white-space: nowrap; flex-shrink: 0;
    box-shadow: 0 2px 14px var(--acc-glow);
    transition: opacity .15s, transform .13s;
  }
  .add-btn:hover  { opacity: .9; transform: translateY(-1px); }
  .add-btn:active { transform: translateY(0); }

  /* ── Responsive ─────────────────────────────────────────── */
  .mobile-only  { display: none; }

  @media (max-width: 768px) {
    .topbar       { padding: 0 10px; gap: 4px; height: 56px; }
    .desktop-only { display: none !important; }
    .mobile-only  { display: flex; }

    /* Period takes remaining space and centers its text so nav buttons
       are always anchored at a fixed position regardless of label length */
    .period       { flex: 1; justify-content: center; min-width: 0; }
    .period-main  { font-size: clamp(14px, 3.5vw, 19px); min-width: 0; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .period-year  { font-size: clamp(12px, 3vw, 16px); }

    /* Compact today button — same row as nav */
    .today-btn    { padding: 5px 9px; font-size: 11px; border-radius: 12px; }

    /* Hide spacer on mobile (period already grows) */
    .spacer       { display: none; }
  }
</style>
