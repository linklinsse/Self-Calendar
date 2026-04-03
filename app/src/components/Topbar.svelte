<script>
  /**
   * Topbar.svelte — App header bar.
   *
   * Uses ViewSwitcher widget (shared with BottomNav).
   * Desktop: hamburger | period | prev/next | Today | ─── | ViewSwitcher | + New
   * Mobile:  hamburger | period | prev/next | ─── | filter-icon
   */

  import ViewSwitcher from './ui/ViewSwitcher.svelte';
  import {
    currentView, cursor, sidebarOpen, filterDrawerOpen, openAddPanel,
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

  <!-- Today (desktop only) -->
  <button class="today-btn desktop-only" onclick={goToday}>Today</button>

  <div class="spacer"></div>

  <!-- ViewSwitcher widget (desktop only) -->
  <div class="desktop-only">
    <ViewSwitcher />
  </div>

  <!-- New event button (desktop only) -->
  <button class="add-btn desktop-only" onclick={() => openAddPanel()} aria-label="New event">
    <span aria-hidden="true">＋</span> New event
  </button>

  <!-- Filter icon (mobile only) -->
  <button
    class="icon-btn mobile-only"
    onclick={() => $filterDrawerOpen = true}
    aria-label="Open filters"
  >
    <svg width="16" height="14" viewBox="0 0 16 14" fill="none" aria-hidden="true">
      <rect x="0" y="0"  width="16" height="1.8" rx=".9" fill="currentColor"/>
      <rect x="2" y="6"  width="12" height="1.8" rx=".9" fill="currentColor"/>
      <rect x="4" y="12" width="8"  height="1.8" rx=".9" fill="currentColor"/>
    </svg>
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
    .topbar       { padding: 0 12px; gap: 6px; height: 56px; }
    .desktop-only { display: none !important; }
    .mobile-only  { display: flex; }
    .period-main  { font-size: clamp(16px, 4vw, 22px); }
  }
</style>
