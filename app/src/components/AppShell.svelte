<script>
  /**
   * AppShell.svelte — Main layout after login.
   *
   * Desktop (>768px): Sidebar fixed left + Main column
   * Mobile  (≤768px): Sidebar as drawer + BottomNav
   */

  import Sidebar          from './Sidebar.svelte';
  import Topbar           from './Topbar.svelte';
  import BottomNav        from './BottomNav.svelte';
  import FilterDrawer     from './ui/FilterDrawer.svelte';
  import CalendarBody     from './calendar/CalendarBody.svelte';
  import EventPanel       from './event/EventPanel.svelte';
  import EventModal       from './event/EventModal.svelte';
  import CalendarSettings from './settings/CalendarSettings.svelte';
  // FIX: CategoryEditor was built but never mounted — categories ＋/✎ did nothing
  import CategoryEditor   from './settings/CategoryEditor.svelte';

  import { onMount }    from 'svelte';
  import { sidebarOpen } from '../lib/stores/index.js';

  // Open sidebar by default on desktop; keep closed on mobile
  onMount(() => {
    if (window.innerWidth >= 769) sidebarOpen.set(true);
  });
</script>

<div class="shell">

  <!-- ── Sidebar (mobile: drawer via CSS) ── -->
  <Sidebar />

  <!-- ── Mobile sidebar backdrop ── -->
  {#if $sidebarOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div
      class="backdrop mobile-only"
      onclick={() => $sidebarOpen = false}
      aria-hidden="true"
    ></div>
  {/if}

  <!-- ── Main area ── -->
  <div class="main">
    <Topbar />
    <CalendarBody />
  </div>

  <!-- ── Mobile bottom nav (CSS-hidden on desktop) ── -->
  <BottomNav />

</div>

<!-- ── Global overlays ── -->
<FilterDrawer />
<EventPanel   />
<EventModal   />
<CalendarSettings />
<CategoryEditor   />

<style>
  .shell {
    display: flex;
    height: 100vh; width: 100vw;
    overflow: hidden;
    position: relative;
  }

  .main {
    flex: 1;
    display: flex; flex-direction: column;
    overflow: hidden;
    min-width: 0;
  }

  /* Mobile sidebar backdrop */
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.55);
    backdrop-filter: blur(3px);
    z-index: 19;
  }

  /* Only show backdrop on mobile — on desktop the sidebar slides inline */
  .mobile-only { display: none; }
  @media (max-width: 768px) {
    .mobile-only { display: block; }
  }

  @media (max-width: 768px) {
    /* Reserve space at bottom for the nav bar */
    .main { padding-bottom: 66px; }
  }
</style>
