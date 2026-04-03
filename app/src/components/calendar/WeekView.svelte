<script>
  /**
   * WeekView.svelte
   *
   * All-day banner row: ONLY true ev.allDay events.
   * Cross-midnight timed events are clipped per-day and rendered as timed blocks:
   *   • start day  → from ev.start to 23:59
   *   • middle days → full-height block 00:00–23:59
   *   • end day    → from 00:00 to ev.end
   */

  import { onMount } from 'svelte';
  import {
    cursor, visibleEvents, openAddPanel, modalEventId,
  } from '../../lib/stores/index.js';
  import {
    weekDays, DAY_ABBR_MON, sameDay, isToday,
    timeToMinutes, hourLabel, formatTime,
    expandEventsForRange, midnight, computeColumns,
  } from '../../lib/utils.js';

  const PX_HR = 58;
  const HOURS = Array.from({ length: 24 }, (_, i) => i);

  let days       = $derived(weekDays($cursor));
  let rangeStart = $derived(days[0]);
  let rangeEnd   = $derived(days[6]);

  let expanded = $derived(expandEventsForRange($visibleEvents, rangeStart, rangeEnd));

  // ── All-day banner row: true allDay + events that fully span the day ──
  let allDayMap = $derived(Object.fromEntries(days.map(d => [
    d.toDateString(),
    expanded.filter(o => {
      if (o.ev.allDay) {
        return midnight(d) >= midnight(o.startDate) && midnight(d) <= midnight(o.endDate);
      }
      // Timed event that completely spans this calendar day (started before, ends after)
      return o.ev.start &&
             midnight(o.startDate) < midnight(d) &&
             midnight(o.endDate)   > midnight(d);
    }),
  ])));

  // ── Timed blocks per day (cross-midnight clipped; full-span excluded) ──
  let timedMap = $derived(Object.fromEntries(days.map(d => [
    d.toDateString(),
    getTimedForDay(expanded, d),
  ])));

  let colMap = $derived(Object.fromEntries(days.map(d => [
    d.toDateString(),
    computeColumns(timedMap[d.toDateString()] ?? []),
  ])));

  /**
   * Return timed occurrences visible for a given day.
   * Events fully spanning the day are excluded (shown in all-day strip).
   * Cross-midnight start/end events are clipped to this day.
   */
  function getTimedForDay(occs, d) {
    const result = [];
    for (const o of occs) {
      if (o.ev.allDay || !o.ev.start) continue;
      const isStartDay = sameDay(o.startDate, d);
      const isEndDay   = sameDay(o.endDate,   d);
      const fullySpans = midnight(o.startDate) < midnight(d) &&
                         midnight(o.endDate)   > midnight(d);
      if (fullySpans) continue; // rendered in all-day strip
      if (isStartDay && isEndDay) {
        result.push(o);
      } else if (isStartDay) {
        result.push({ ...o, ev: { ...o.ev, end: '23:59' }, _clip: 'start' });
      } else if (isEndDay) {
        result.push({ ...o, ev: { ...o.ev, start: '00:00' }, _clip: 'end' });
      }
    }
    return result;
  }

  function evStyle(occ, col, cols) {
    const sm  = timeToMinutes(occ.ev.start ?? '00:00');
    const em  = timeToMinutes(occ.ev.end   ?? '23:59');
    const top = Math.round((sm / 60) * PX_HR);
    const ht  = Math.max(22, Math.round(((em - sm) / 60) * PX_HR));
    const pct = 100 / cols;
    return `top:${top}px; height:${ht}px; left:calc(${col * pct}% + 2px); width:calc(${pct}% - 4px);`;
  }

  function isShort(occ) {
    const sm = timeToMinutes(occ.ev.start ?? '00:00');
    const em = timeToMinutes(occ.ev.end   ?? '23:59');
    return Math.max(22, Math.round(((em - sm) / 60) * PX_HR)) < 32;
  }

  function onSlotClick(d, h) {
    openAddPanel(new Date(d), String(h).padStart(2,'0') + ':00');
  }

  let bodyEl;
  onMount(() => { if (bodyEl) bodyEl.scrollTop = 7 * PX_HR; });
</script>

<div class="week-view">

  <!-- Header row -->
  <div class="wk-header">
    <div class="gutter-head"></div>
    {#each days as d, i (d.toDateString())}
      <div class="col-head" class:today={isToday(d)}>
        <span class="col-dow">{DAY_ABBR_MON[i]}</span>
        <span class="col-num">{d.getDate()}</span>
        <!-- All-day pills (true allDay only) -->
        <div class="allday-row">
          {#each allDayMap[d.toDateString()] ?? [] as occ (occ.ev.id + '-' + occ.startDate.toISOString())}
            <button
              class="allday-pill"
              style="background:{occ.ev.color}; color:#1a0812"
              onclick={e => { e.stopPropagation(); $modalEventId = occ.ev.id }}
              aria-label="{occ.ev.title}"
            >{occ.ev.title}</button>
          {/each}
        </div>
      </div>
    {/each}
  </div>

  <!-- Time grid -->
  <div class="wk-body" bind:this={bodyEl}>
    <div class="time-grid">

      <div class="time-gutter" aria-hidden="true">
        {#each HOURS as h}
          <div class="hour-lbl" style="height:{PX_HR}px">{hourLabel(h)}</div>
        {/each}
      </div>

      {#each days as d (d.toDateString())}
        <div class="day-col">
          {#each HOURS as h}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <div
              class="hour-slot"
              style="height:{PX_HR}px"
              role="button" tabindex="-1"
              aria-label="Add event {hourLabel(h) || '12 AM'} on {d.toLocaleDateString()}"
              onclick={() => onSlotClick(d, h)}
              onkeydown={e => e.key === 'Enter' && onSlotClick(d, h)}
            ></div>
          {/each}

          {#each colMap[d.toDateString()] ?? [] as item (item.occ.ev.id + '-' + (item.occ._clip ?? '') + '-' + item.occ.startDate.toISOString())}
            {@const clipped = !!item.occ._clip}
            <button
              class="ev-block"
              class:short={isShort(item.occ)}
              class:clipped-start={item.occ._clip === 'start'}
              class:clipped-end={item.occ._clip === 'end'}
              style="{evStyle(item.occ, item.col, item.cols)} background:{item.occ.ev.color}44; border-left:3px solid {item.occ.ev.color};"
              onclick={e => { e.stopPropagation(); $modalEventId = item.occ.ev.id }}
              aria-label="{item.occ.ev.title}"
            >
              <span class="ev-title" style="color:{item.occ.ev.color}">{item.occ.ev.title}</span>
              {#if !isShort(item.occ)}
                <span class="ev-time" style="color:{item.occ.ev.color}">
                  {#if item.occ._clip === 'end'}↩ {/if}{formatTime(item.occ.ev.start)}{#if item.occ._clip === 'start'} →{/if}
                </span>
              {/if}
            </button>
          {/each}

        </div>
      {/each}

    </div>
  </div>

</div>

<style>
  .week-view { height: 100%; display: flex; flex-direction: column; overflow: hidden; }

  /* ── Header ── */
  .wk-header {
    display: grid; grid-template-columns: 54px repeat(7,1fr);
    background: var(--bg-surf); border-bottom: 1px solid var(--bdr-soft);
    flex-shrink: 0;
  }
  .gutter-head { border-right: 1px solid var(--bdr-soft); }

  .col-head {
    border-right: 1px solid var(--bdr-soft);
    padding: 8px 4px 6px;
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    min-height: 54px;
  }
  .col-head:last-child { border-right: none; }

  .col-dow {
    font-size: var(--fs-xs, 13px); color: var(--t2);
    font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em;
  }
  .col-num {
    font-family: var(--f-display); font-size: 22px; font-weight: 300; color: var(--t1);
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    transition: background .12s, color .12s;
  }
  .col-head.today .col-num { background: var(--acc); color: #1a0812; font-weight: 600; }

  /* All-day pills in header — bigger and more readable */
  .allday-row { width: 100%; display: flex; flex-direction: column; gap: 3px; }
  .allday-pill {
    width: 100%; font-size: 12px; font-weight: 700;
    padding: 3px 6px; border-radius: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
    transition: opacity .12s;
  }
  .allday-pill:hover { opacity: .78; }

  /* ── Body ── */
  .wk-body { flex: 1; overflow-y: auto; overflow-x: auto; }
  .time-grid { display: grid; grid-template-columns: 54px repeat(7,1fr); min-width: 520px; }

  .time-gutter { border-right: 1px solid var(--bdr-soft); }
  .hour-lbl {
    border-bottom: 1px solid var(--bdr-soft);
    display: flex; align-items: flex-start; justify-content: flex-end;
    padding: 4px 7px 0 0;
    font-size: 11px; font-weight: 500; color: var(--t2);
    flex-shrink: 0;
  }

  .day-col { border-right: 1px solid var(--bdr-soft); position: relative; }
  .day-col:last-child { border-right: none; }

  .hour-slot {
    border-bottom: 1px solid var(--bdr-soft);
    cursor: pointer; transition: background .12s;
  }
  .hour-slot:hover { background: var(--acc-bg); }

  /* Timed event blocks */
  .ev-block {
    position: absolute;
    border-radius: 5px; padding: 3px 6px;
    overflow: hidden; z-index: 1; text-align: left;
    cursor: pointer; transition: opacity .12s, filter .12s;
    min-width: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
  }
  .ev-block:hover { opacity: .88; filter: brightness(1.08); }

  /* Cross-midnight visual cues */
  .ev-block.clipped-start { border-bottom-left-radius: 0; border-bottom-right-radius: 0; }
  .ev-block.clipped-end   { border-top-left-radius: 0;    border-top-right-radius: 0; }

  .ev-title {
    display: block; font-size: 12px; font-weight: 700;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    line-height: 1.2;
  }
  .ev-block.short .ev-title { font-size: 11px; font-weight: 700; }
  .ev-time { display: block; font-size: 10px; opacity: .85; margin-top: 1px; font-weight: 500; }

  @media (max-width: 768px) {
    .col-num { font-size: 17px; width: 28px; height: 28px; }
  }
</style>
