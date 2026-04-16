<script>
  /**
   * Sidebar.svelte — Main left sidebar shell.
   *
   * Desktop collapse: the .sidebar shell animates width 264px→0.
   * Content lives in .sidebar-inner (fixed 264px wide) so text never
   * reflows during the animation — eliminates the logo glitch.
   *
   * Mobile: position:fixed slide-in drawer via transform.
   */

  import CalendarList from './sidebar/CalendarList.svelte';
  import CategoryList from './sidebar/CategoryList.svelte';
  import ThemePicker  from './settings/ThemePicker.svelte';
  import { sidebarOpen, logoutUser } from '../lib/stores/index.js';
</script>

<aside class="sidebar" class:open={$sidebarOpen} aria-label="Sidebar">

  <!-- Inner wrapper: fixed 264px so content never reflows during width animation -->
  <div class="sidebar-inner">

    <!-- ── Sticky top: Brand ── -->
    <div class="sidebar-top">
      <div class="logo">Self <em>Calendar</em></div>
    </div>

    <!-- ── Scrollable middle: calendars + categories ── -->
    <div class="sidebar-scroll">
      <div class="section">
        <CalendarList />
      </div>

      <div class="divider" aria-hidden="true"></div>

      <div class="section">
        <CategoryList />
      </div>
    </div>

    <!-- ── Sticky bottom: Theme + Sign out ── -->
    <div class="sidebar-bottom">
      <div class="section theme-section">
        <p class="section-label">Theme</p>
        <ThemePicker />
      </div>

      <footer class="sb-footer">
        <button class="foot-btn" onclick={logoutUser}>
          <span aria-hidden="true">↩</span> Sign out
        </button>
      </footer>
    </div>

  </div><!-- /sidebar-inner -->

</aside>

<style>
  /* ── Shell — handles width animation only ───────────────── */
  .sidebar {
    width: 264px;
    height: 100vh;
    background: var(--bg-surf);
    border-right: 1px solid var(--bdr-soft);
    flex-shrink: 0;
    z-index: 20;
    overflow: hidden; /* clips inner content during collapse */
    transition: width .30s cubic-bezier(.16,1,.3,1),
                border-color .30s;
  }

  /* Desktop collapse: shrink to 0, content is clipped by overflow:hidden */
  @media (min-width: 769px) {
    .sidebar:not(.open) {
      width: 0;
      border-color: transparent;
    }
  }

  /* Mobile: fixed slide-in drawer */
  @media (max-width: 768px) {
    .sidebar {
      position: fixed; left: 0; top: 0; bottom: 0;
      width: 264px; /* always full width on mobile, transform handles hide/show */
      transform: translateX(-100%);
      box-shadow: 6px 0 40px rgba(0,0,0,.5);
      transition: transform .32s cubic-bezier(.16,1,.3,1);
    }
    .sidebar.open { transform: translateX(0); }
  }

  /* ── Inner wrapper — fixed width, never reflows ─────────── */
  .sidebar-inner {
    width: 264px;
    min-width: 264px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* ── Sticky top (logo) ───────────────────────────────────── */
  .sidebar-top {
    flex-shrink: 0;
    padding: 20px 14px 0;
  }

  /* ── Scrollable middle (calendars + categories) ──────────── */
  .sidebar-scroll {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0 14px;
  }

  /* ── Sticky bottom (theme + sign out) ───────────────────── */
  .sidebar-bottom {
    flex-shrink: 0;
    padding: 0 14px 16px;
    border-top: 1px solid var(--bdr-soft);
  }

  @media (max-width: 768px) {
    .sidebar-bottom {
      padding-bottom: calc(66px + 16px);
    }
  }

  /* ── Logo ───────────────────────────────────────────────── */
  .logo {
    font-family: var(--f-display);
    font-size: var(--fs-xxl, 34px); font-weight: 400;
    color: var(--acc); letter-spacing: .03em;
    padding: 0 8px 18px;
    flex-shrink: 0; line-height: 1;
    white-space: nowrap; /* prevent any wrapping at any width */
  }
  .logo em { font-style: italic; }

  /* ── Sections ───────────────────────────────────────────── */
  .section        { flex-shrink: 0; padding: 8px 0; }
  .theme-section  { padding-bottom: 4px; padding-top: 10px; }

  .section-label {
    font-size: 10px; font-weight: 500; color: var(--t3);
    text-transform: uppercase; letter-spacing: .10em;
    padding: 0 2px 6px 8px;
  }

  /* ── Divider ────────────────────────────────────────────── */
  .divider {
    height: 1px; background: var(--bdr-soft);
    margin: 4px 8px; flex-shrink: 0;
  }

  /* ── Footer ─────────────────────────────────────────────── */
  .sb-footer {
    padding-top: 10px; border-top: 1px solid var(--bdr-soft);
    flex-shrink: 0; margin-top: 8px;
  }
  .foot-btn {
    display: flex; align-items: center; gap: 10px;
    width: 100%; padding: 9px 8px; border-radius: var(--r-s);
    font-size: var(--fs-sm, 15px); color: var(--t3);
    transition: color .18s, background .18s;
    white-space: nowrap;
  }
  .foot-btn:hover { color: var(--acc); background: var(--acc-bg); }
</style>
