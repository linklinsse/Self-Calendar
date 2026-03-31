<script>
  import {
    cursor, currentView, visibleEvents,
    openAddPanel, modalEventId,
  } from '../../lib/stores/index.js';
  import {
    buildMonthGrid, DAY_ABBR_MON, sameDay, isToday,
    expandEventsForRange, midnight,
  } from '../../lib/utils.js';

  $: year  = $cursor.getFullYear();
  $: month = $cursor.getMonth();
  $: grid  = buildMonthGrid(year, month);
  $: weeks = Math.ceil(grid.length / 7);  // explicit row count for banner-layer
  $: rangeStart = grid[0]             ?? new Date(year, month, 1);
  $: rangeEnd   = grid[grid.length-1] ?? new Date(year, month + 1, 0);

  $: expanded = expandEventsForRange($visibleEvents, rangeStart, rangeEnd);

  // Only truly spanning (multi-day) events go to the banner-layer.
  // Single-day allDay and timed events render inline inside each cell.
  $: spanningOccs     = expanded.filter(o => !sameDay(o.startDate, o.endDate));
  $: timedOccs        = expanded.filter(o =>  sameDay(o.startDate, o.endDate) && !o.ev.allDay);
  $: singleAllDayOccs = expanded.filter(o =>  sameDay(o.startDate, o.endDate) &&  o.ev.allDay);

  $: cellEvsByDay = (() => {
    const m = new Map();
    for (const d of grid) {
      const allDay = singleAllDayOccs.filter(o => sameDay(o.startDate, d));
      const timed  = timedOccs.filter(o => sameDay(o.startDate, d));
      const timedShown = Math.max(0, 3 - allDay.length);
      const totalShown = allDay.length + Math.min(timed.length, timedShown);
      m.set(d.toDateString(), { allDay, timed, all: [...allDay, ...timed], timedShown, totalShown });
    }
    return m;
  })();

  function getSpanRows(occ) {
    const s = midnight(occ.startDate), e = midnight(occ.endDate);
    const rows = [];
    let gi = grid.findIndex(d => midnight(d) >= s);
    if (gi < 0) gi = 0;
    while (gi < grid.length) {
      const rowStart = gi - (gi % 7), col = gi % 7;
      let span = 0;
      for (let c = col; c < 7 && gi + (c - col) < grid.length; c++) {
        if (midnight(grid[gi + (c - col)]) > e) break;
        span++;
      }
      if (span > 0) rows.push({ rowStart, col, span, gi });
      gi = rowStart + 7;
      if (gi >= grid.length || midnight(grid[gi]) > e) break;
    }
    return rows;
  }

  $: spanMap = spanningOccs.map(occ => ({ occ, rows: getSpanRows(occ) }));

  $: slotAssignments = (() => {
    const slotUsed = Array.from({ length: grid.length }, () => new Set());
    const result   = new Map();
    for (const { occ, rows } of spanMap) {
      let slot = 0, found = false;
      while (!found) {
        found = true;
        outer: for (const { rowStart, col, span } of rows)
          for (let i = col; i < col + span; i++)
            if (rowStart + i < grid.length && slotUsed[rowStart + i].has(slot)) { found = false; break outer; }
        if (!found) slot++;
      }
      for (const { rowStart, col, span } of rows)
        for (let i = col; i < col + span; i++)
          if (rowStart + i < grid.length) slotUsed[rowStart + i].add(slot);
      result.set(occ.ev.id + '-' + occ.startDate.toISOString(), slot);
    }
    return result;
  })();

  $: bannerRowsByCell = (() => {
    const m = new Map();
    for (const { occ, rows } of spanMap) {
      const slot = slotAssignments.get(occ.ev.id + '-' + occ.startDate.toISOString()) ?? 0;
      for (const { rowStart, col, span } of rows)
        for (let i = col; i < col + span; i++) {
          const ci = rowStart + i;
          if (ci < grid.length) m.set(ci, Math.max(m.get(ci) ?? 0, slot + 1));
        }
    }
    return m;
  })();

  const BANNER_H   = 22;
  const BANNER_GAP =  2;
  const CELL_TOP   = 30;
  const MAX_DOTS   =  5;

  function onCellClick(d)     { cursor.set(new Date(d)); $currentView = 'day'; }
  function onOccClick(occ, e) { e.stopPropagation(); $modalEventId = occ.ev.id; }
</script>

<div class="month-view">

  <div class="dow-row" role="row">
    {#each DAY_ABBR_MON as name}
      <span class="dow-cell" role="columnheader">{name}</span>
    {/each}
  </div>

  <div class="grid-wrap">

    <!-- Layer 1: cells -->
    <div
      class="cell-layer"
      role="grid"
      style="grid-template-rows: repeat({weeks}, 1fr)"
    >
      {#each grid as d, ci (d.toISOString())}
        {@const outside  = d.getMonth() !== month}
        {@const today    = isToday(d)}
        {@const dayEvs   = cellEvsByDay.get(d.toDateString()) ?? { allDay: [], timed: [], all: [] }}
        {@const slots    = bannerRowsByCell.get(ci) ?? 0}

        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <div
          class="cell"
          class:outside class:today
          class:has-ev={dayEvs.all.length > 0}
          role="gridcell"
          aria-label="{d.toLocaleDateString()}{today ? ', today' : ''}"
          tabindex="0"
          on:click={() => onCellClick(d)}
          on:keydown={e => e.key === 'Enter' && onCellClick(d)}
        >
          <span class="cell-num">{d.getDate()}</span>

          <!-- Space reserved for spanning banner rows above -->
          <div class="banner-spacer" style="height:{slots * (BANNER_H + BANNER_GAP)}px"></div>

          <!-- Inline events: allDay first, then timed -->
          <div class="cell-evs">
            {#each dayEvs.allDay as occ (occ.ev.id + '-' + occ.startDate.toISOString())}
              <button
                class="ev-pill ev-pill--allday"
                style="background:{occ.ev.color}; color:#1a0812"
                on:click={e => onOccClick(occ, e)}
                aria-label="{occ.ev.title} (all day)"
              >{occ.ev.title}</button>
            {/each}

            {#each dayEvs.timed.slice(0, dayEvs.timedShown) as occ (occ.ev.id + '-' + occ.startDate.toISOString())}
              <button
                class="ev-pill"
                style="background:{occ.ev.color}42; color:{occ.ev.color}; border-left:3px solid {occ.ev.color}"
                on:click={e => onOccClick(occ, e)}
                aria-label="{occ.ev.title}"
              >
                <span class="pill-dot" style="background:{occ.ev.color}"></span>
                {occ.ev.title}
              </button>
            {/each}

            {#if dayEvs.all.length > dayEvs.totalShown}
              <div class="overflow-row" aria-label="{dayEvs.all.length - dayEvs.totalShown} more events">
                {#each dayEvs.all.slice(dayEvs.totalShown, dayEvs.totalShown + MAX_DOTS) as occ}
                  <button
                    class="ov-dot"
                    style="background:{occ.ev.color}"
                    on:click={e => onOccClick(occ, e)}
                    aria-label={occ.ev.title}
                    title={occ.ev.title}
                  ></button>
                {/each}
                {#if dayEvs.all.length - dayEvs.totalShown > MAX_DOTS}
                  <span class="ov-ellipsis">…</span>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Layer 2: multi-day spanning banners -->
    <div
      class="banner-layer"
      aria-hidden="true"
      style="grid-template-rows: repeat({weeks}, 1fr)"
    >
      {#each spanMap as { occ, rows }}
        {@const key  = occ.ev.id + '-' + occ.startDate.toISOString()}
        {@const slot = slotAssignments.get(key) ?? 0}
        {#each rows as row}
          {@const isStart = sameDay(occ.startDate, grid[row.gi])}
          {@const isEnd   = sameDay(occ.endDate,   grid[row.gi + row.span - 1])}
          <button
            class="ev-banner"
            aria-label="{occ.ev.title}"
            title="{occ.ev.title}"
            style="
              grid-column: {row.col + 1} / span {row.span};
              grid-row: {Math.floor(row.rowStart / 7) + 1};
              margin-top: {CELL_TOP + slot * (BANNER_H + BANNER_GAP)}px;
              height: {BANNER_H}px;
              background: {occ.ev.color};
              border-radius: {isStart ? '5px' : '0'} {isEnd ? '5px' : '0'} {isEnd ? '5px' : '0'} {isStart ? '5px' : '0'};
              margin-left: {isStart ? '3px' : '0'};
              margin-right: {isEnd   ? '3px' : '0'};
            "
            on:click|stopPropagation={() => $modalEventId = occ.ev.id}
          >
            {#if isStart}
              <span class="banner-title">{occ.ev.title}</span>
            {/if}
          </button>
        {/each}
      {/each}
    </div>

  </div>
</div>

<style>
  .month-view { height: 100%; display: flex; flex-direction: column; overflow: hidden; }

  .dow-row {
    display: grid; grid-template-columns: repeat(7,1fr);
    background: var(--bg-surf); border-bottom: 1px solid var(--bdr-soft); flex-shrink: 0;
  }
  .dow-cell {
    text-align: center; padding: 9px 0;
    font-size: var(--fs-xs,13px); font-weight: 600; color: var(--t2);
    text-transform: uppercase; letter-spacing: .07em;
  }

  .grid-wrap {
    flex: 1; overflow: hidden;
    position: relative;
  }

  .cell-layer,
  .banner-layer {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    /* grid-template-rows set via inline style (repeat(weeks, 1fr))
       so both layers always have the EXACT same number of rows */
  }

  .cell-layer {
    position: absolute; inset: 0;
    z-index: 0;
  }

  .banner-layer {
    position: absolute; inset: 0;
    z-index: 1;
    pointer-events: none;
    align-items: start;
  }

  /* ── Cells ── */
  .cell {
    border-right: 1px solid var(--bdr-soft);
    border-bottom: 1px solid var(--bdr-soft);
    padding: 4px 4px 2px;
    display: flex; flex-direction: column;
    overflow: hidden; cursor: pointer;
    transition: background .12s; min-height: 0;
  }
  .cell:nth-child(7n) { border-right: none; }
  .cell:hover         { background: rgba(244,184,200,.03); }
  .cell:focus-visible { outline: 2px solid var(--acc); outline-offset: -2px; }
  .cell.outside       { background: transparent; }
  .cell.outside .cell-num { color: var(--t3); }

  .cell-num {
    font-size: var(--fs-sm,15px); color: var(--t1);
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background .12s, color .12s;
  }
  .cell.today .cell-num { background: var(--acc); color: #1a0812; font-weight: 700; }

  .banner-spacer { flex-shrink: 0; }

  .cell-evs { display: flex; flex-direction: column; gap: 2px; overflow: hidden; flex: 1; }

  /* Timed event pills */
  .ev-pill {
    display: flex; align-items: center; gap: 4px;
    font-size: 12px; font-weight: 600;
    padding: 2px 5px; border-radius: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    text-align: left; line-height: 1.5; transition: opacity .12s;
  }
  .ev-pill:hover { opacity: .78; }

  /* Single-day allDay pills — solid, dark text */
  .ev-pill--allday {
    font-size: 11px; font-weight: 700;
    padding: 2px 7px; border-radius: 4px;
    color: #1a0812 !important;
  }
  .pill-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

  .overflow-row { display: flex; align-items: center; gap: 3px; padding: 2px 5px; }
  .ov-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    pointer-events: all;
    transition: transform .12s;
  }
  .ov-dot:hover { transform: scale(1.3); }
  .ov-ellipsis  { font-size: 10px; color: var(--t2); }

  /* ── Spanning banners ── */
  .ev-banner {
    align-self: start;
    display: flex; align-items: center;
    overflow: hidden; padding: 0 7px;
    cursor: pointer;
    pointer-events: all;
    transition: opacity .12s, filter .12s;
    box-shadow: 0 1px 3px rgba(0,0,0,.25);
  }
  .ev-banner:hover { opacity: .85; filter: brightness(1.08); }

  .banner-title {
    font-size: 11px; font-weight: 700; color: #1a0812;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  @media (max-width: 768px) {
    .cell      { padding: 3px 2px 1px; }
    .cell-num  { font-size: var(--fs-xs,13px); width: 22px; height: 22px; }
    .ev-pill   { font-size: 10px; }
  }
  @media (max-width: 380px) {
    .ev-pill { display: none; }
    .cell.has-ev .cell-num { box-shadow: 0 0 0 2px var(--acc); }
  }
</style>
