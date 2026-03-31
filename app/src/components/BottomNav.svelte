<script>
  /**
   * BottomNav.svelte — Mobile bottom bar.
   *
   * FIX: ViewSwitcher (3 buttons) + Filter was 5+ items = too crowded.
   * Solution: ViewSwitcher is now a compact inline row, Filter is merged
   * into the Sidebar (the ☰ Menu opens both calendars+categories filters).
   * Bottom bar: Menu | ← M W D → | ＋ FAB | Today
   * That's 4 logical items, clean on any phone width.
   */
  import ViewSwitcher from './ui/ViewSwitcher.svelte';
  import { sidebarOpen, cursor, openAddPanel } from '../lib/stores/index.js';

  function goToday() { cursor.set(new Date()); }
</script>

<nav class="bottom-nav" aria-label="Mobile navigation">

  <!-- Sidebar / filter toggle -->
  <button class="bn-btn" on:click={() => $sidebarOpen = !$sidebarOpen} aria-label="Menu and filters">
    <svg width="20" height="15" viewBox="0 0 20 15" fill="none" aria-hidden="true">
      <rect y="0"   width="20" height="2" rx="1" fill="currentColor"/>
      <rect y="6.5" width="15" height="2" rx="1" fill="currentColor"/>
      <rect y="13"  width="20" height="2" rx="1" fill="currentColor"/>
    </svg>
    <span>Menu</span>
  </button>

  <!-- View switcher (compact M/W/D) -->
  <ViewSwitcher compact={true} />

  <!-- FAB: add event -->
  <button class="fab" on:click={() => openAddPanel()} aria-label="Add new event">
    <span aria-hidden="true">＋</span>
  </button>

  <!-- Today -->
  <button class="bn-btn" on:click={goToday} aria-label="Go to today">
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="9" cy="9" r="7"  stroke="currentColor" stroke-width="1.6"/>
      <circle cx="9" cy="9" r="2"  fill="currentColor"/>
    </svg>
    <span>Today</span>
  </button>

</nav>

<style>
  .bottom-nav { display: none; }

  @media (max-width: 768px) {
    .bottom-nav {
      display: flex; position: fixed; bottom: 0; left: 0; right: 0;
      height: 66px;
      background: var(--bg-surf); border-top: 1px solid var(--bdr-soft);
      align-items: center; justify-content: space-around;
      padding: 0 6px;
      padding-bottom: env(safe-area-inset-bottom, 0px);
      z-index: 10;
    }
    .bn-btn {
      display: flex; flex-direction: column; align-items: center; gap: 3px;
      padding: 6px 10px; border-radius: var(--r-m);
      color: var(--t3); font-size: var(--fs-xs, 13px);
      min-width: 44px; min-height: 44px; justify-content: center;
      transition: color .14s;
    }
    .bn-btn:hover { color: var(--acc); }
    .fab {
      width: 52px; height: 52px; border-radius: 50%;
      background: linear-gradient(135deg, var(--acc), var(--acc-dim));
      color: #1a0812; font-size: 26px;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 3px 16px var(--acc-glow); flex-shrink: 0;
      transition: transform .13s, opacity .14s;
    }
    .fab:hover  { transform: scale(1.08); }
    .fab:active { transform: scale(.92); opacity: .9; }
  }
</style>
