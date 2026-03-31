<script>
  /**
   * MiniCalendar.svelte — Compact month-grid widget in the sidebar.
   *
   * Has its own navigation state so browsing it doesn't affect the main view.
   * Clicking a day: sets cursor + switches to day view.
   */

  import { cursor, currentView } from '../../lib/stores.js';
  import { buildMonthGrid, MONTH_ABBR, DOW_LETTERS, sameDay, isToday }
    from '../../lib/utils.js';

  // Local mini-cursor — independent from the main cursor
  let miniYear  = $cursor.getFullYear();
  let miniMonth = $cursor.getMonth();

  $: grid = buildMonthGrid(miniYear, miniMonth);

  function prevMini() {
    if (miniMonth === 0) { miniMonth = 11; miniYear--; }
    else miniMonth--;
  }
  function nextMini() {
    if (miniMonth === 11) { miniMonth = 0; miniYear++; }
    else miniMonth++;
  }

  function pickDay(d) {
    if (d.getMonth() !== miniMonth) return; // ignore filler days
    cursor.set(new Date(d));
    $currentView = 'day';
  }

  $: isSelected = (d) =>
    d.getMonth() === miniMonth && sameDay(d, $cursor);
</script>

<div class="mini-cal" aria-label="Mini calendar">
  <!-- Month header -->
  <div class="mc-hdr">
    <button class="mc-nav" on:click={prevMini} aria-label="Previous month">‹</button>
    <span class="mc-label">
      {MONTH_ABBR[miniMonth]} {miniYear}
    </span>
    <button class="mc-nav" on:click={nextMini} aria-label="Next month">›</button>
  </div>

  <!-- Day-of-week labels -->
  <div class="mc-grid">
    {#each DOW_LETTERS as l}
      <span class="mc-dow" aria-hidden="true">{l}</span>
    {/each}

    <!-- Day cells -->
    {#each grid as d (d.toISOString())}
      <button
        class="mc-day"
        class:other   ={d.getMonth() !== miniMonth}
        class:today   ={isToday(d)}
        class:selected={isSelected(d) && !isToday(d)}
        on:click={() => pickDay(d)}
        aria-label={d.toLocaleDateString()}
        aria-current={isToday(d) ? 'date' : undefined}
        tabindex={d.getMonth() !== miniMonth ? -1 : 0}
      >
        {d.getDate()}
      </button>
    {/each}
  </div>
</div>

<style>
  .mini-cal { padding: 0 4px 8px; }

  .mc-hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 7px;
  }
  .mc-label {
    font-size: 11px; font-weight: 500;
    color: var(--t2); letter-spacing: .05em;
  }
  .mc-nav {
    width: 22px; height: 22px; border-radius: 5px;
    color: var(--t3); font-size: 15px;
    display: flex; align-items: center; justify-content: center;
    transition: color .14s, background .14s;
  }
  .mc-nav:hover { color: var(--acc); background: var(--acc-bg); }

  .mc-grid {
    display: grid; grid-template-columns: repeat(7,1fr);
  }
  .mc-dow {
    text-align: center; font-size: 9px; color: var(--t3);
    padding: 2px 0 5px; text-transform: uppercase; letter-spacing: .04em;
  }

  .mc-day {
    text-align: center; font-size: 11px; color: var(--t2);
    padding: 3px; border-radius: 5px;
    min-height: 22px;
    display: flex; align-items: center; justify-content: center;
    transition: background .12s, color .12s;
  }
  .mc-day:hover:not(.other) { background: var(--acc-bg); color: var(--acc); }
  .mc-day.other    { color: var(--t3); pointer-events: none; }
  .mc-day.today    { background: var(--acc); color: #1a0812; font-weight: 600; }
  .mc-day.selected { background: var(--acc-bg); color: var(--acc); }
</style>
