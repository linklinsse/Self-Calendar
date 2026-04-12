<script>
  /**
   * DayView.svelte
   *
   * All-day strip: ONLY true ev.allDay events.
   * Cross-midnight timed events are clipped to the visible portion of this day.
   */

  import { onMount } from 'svelte';
  import {
    cursor, visibleEvents, openAddPanel, modalEventId,
  } from '../../lib/stores/index.js';
  import {
    sameDay, isToday, timeToMinutes,
    hourLabel, formatTime, formatLongDay,
    expandEventsForRange, midnight, computeColumns,
  } from '../../lib/utils.js';

  const PX_HR = 62;
  const HOURS = Array.from({ length: 24 }, (_, i) => i);

  let today   = $derived(isToday($cursor));
  let heading = $derived(formatLongDay($cursor));
  let dayStart = $derived(midnight($cursor));
  let dayEnd   = $derived(midnight($cursor));
  let expanded = $derived(expandEventsForRange($visibleEvents, dayStart, dayEnd));

  // All-day strip: true allDay + timed events that fully span this day
  let allDayOccs = $derived(expanded.filter(o => {
    if (o.ev.allDay) return true;
    if (!o.ev.start) return false;
    // Fully spans: started before midnight, ends after midnight
    return midnight(o.startDate) < midnight($cursor) &&
           midnight(o.endDate)   > midnight($cursor);
  }));

  // Timed grid: normal + cross-midnight clipped; full-span excluded
  let timedOccs = $derived((() => {
    const d = $cursor;
    const result = [];
    for (const o of expanded) {
      if (o.ev.allDay || !o.ev.start) continue;
      const isStartDay = sameDay(o.startDate, d);
      const isEndDay   = sameDay(o.endDate,   d);
      const fullySpans = midnight(o.startDate) < midnight(d) &&
                         midnight(o.endDate)   > midnight(d);
      if (fullySpans) continue; // shown in all-day strip
      if (isStartDay && isEndDay) {
        result.push(o);
      } else if (isStartDay) {
        result.push({ ...o, ev: { ...o.ev, end: '23:59' }, _clip: 'start' });
      } else if (isEndDay) {
        result.push({ ...o, ev: { ...o.ev, start: '00:00' }, _clip: 'end' });
      }
    }
    return result;
  })());

  let columns = $derived(computeColumns(timedOccs));

  function evStyle(occ, col, cols) {
    const sm  = timeToMinutes(occ.ev.start ?? '00:00');
    const em  = timeToMinutes(occ.ev.end   ?? '23:59');
    const top = Math.round((sm / 60) * PX_HR);
    const ht  = Math.max(34, Math.round(((em - sm) / 60) * PX_HR));
    if (cols === 1) return `top:${top}px; height:${ht}px; left:10px; right:10px;`;
    const pct = 100 / cols;
    return `top:${top}px; height:${ht}px; left:calc(${col * pct}% + 2px); width:calc(${pct}% - 4px);`;
  }

  function isShort(occ) {
    const sm = timeToMinutes(occ.ev.start ?? '00:00');
    const em = timeToMinutes(occ.ev.end   ?? '23:59');
    return Math.max(34, Math.round(((em - sm) / 60) * PX_HR)) < 44;
  }

  function onSlotClick(h) {
    openAddPanel(new Date($cursor), String(h).padStart(2,'0') + ':00');
  }

  let bodyEl;
  onMount(() => { if (bodyEl) bodyEl.scrollTop = 7 * PX_HR; });
</script>

<div class="day-view">

  <div class="day-header">
    <div class="heading-row">
      <h2 class="heading">{heading}</h2>
      {#if today}<span class="today-badge">Today</span>{/if}
    </div>
    <p class="ev-count" aria-live="polite">
      {expanded.length} event{expanded.length !== 1 ? 's' : ''}
    </p>

    {#if allDayOccs.length > 0}
      <div class="allday-strip">
        {#each allDayOccs as occ (occ.ev.id + '-' + occ.startDate.toISOString())}
          <button
            class="allday-pill"
            style="background:{occ.ev.color}; color:#1a0812"
            onclick={() => $modalEventId = occ.ev.id}
            aria-label="{occ.ev.title} (all day)"
          >{occ.ev.title}</button>
        {/each}
      </div>
    {/if}
  </div>

  <div class="day-body" bind:this={bodyEl}>

    <div class="time-col" aria-hidden="true">
      {#each HOURS as h}
        <div class="hour-lbl" style="height:{PX_HR}px">{hourLabel(h)}</div>
      {/each}
    </div>

    <div class="event-col">
      {#each HOURS as h}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div
          class="hour-slot"
          style="height:{PX_HR}px"
          role="button" tabindex="-1"
          aria-label="Add event at {hourLabel(h) || '12 AM'}"
          onclick={() => onSlotClick(h)}
          onkeydown={e => e.key === 'Enter' && onSlotClick(h)}
        ></div>
      {/each}

      {#each columns as item (item.occ.ev.id + '-' + (item.occ._clip ?? '') + '-' + item.occ.startDate.toISOString())}
        {@const short = isShort(item.occ)}
        <button
          class="ev-block"
          class:short
          class:clipped-start={item.occ._clip === 'start'}
          class:clipped-end={item.occ._clip === 'end'}
          style="{evStyle(item.occ, item.col, item.cols)} background:{item.occ.ev.color}40; border-left:4px solid {item.occ.ev.color};"
          onclick={e => { e.stopPropagation(); $modalEventId = item.occ.ev.id }}
          aria-label="{item.occ.ev.title}"
        >
          <span class="ev-title" style="color:{item.occ.ev.color}">{item.occ.ev.title}</span>
          {#if !short}
            <span class="ev-time" style="color:{item.occ.ev.color}">
              {#if item.occ._clip === 'end'}↩ {/if}{formatTime(item.occ.ev.start)} – {formatTime(item.occ.ev.end)}{#if item.occ._clip === 'start'} →{/if}
            </span>
            {#if item.occ.ev.adresse && !item.occ._clip}
              <span class="ev-loc">📍 {item.occ.ev.adresse}</span>
            {/if}
          {/if}
        </button>
      {/each}
    </div>

  </div>
</div>

<style>
  .day-view { height: 100%; display: flex; flex-direction: column; overflow: hidden; }

  .day-header {
    padding: 16px 22px 12px;
    background: var(--bg-surf); border-bottom: 1px solid var(--bdr-soft);
    flex-shrink: 0;
  }
  .heading-row { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
  .heading {
    font-family: var(--f-display);
    font-size: var(--fs-xxl, 34px);
    font-weight: 300; letter-spacing: .02em; color: var(--t1);
  }
  .today-badge {
    font-size: var(--fs-xs, 13px);
    font-style: italic; color: var(--acc-dim); letter-spacing: .04em;
  }
  .ev-count { font-size: var(--fs-xs, 13px); color: var(--t2); margin-top: 2px; }

  .allday-strip { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
  .allday-pill {
    padding: 4px 12px; border-radius: 20px;
    font-size: 13px; font-weight: 700;
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
    transition: opacity .12s;
  }
  .allday-pill:hover { opacity: .78; }

  .day-body { flex: 1; overflow-y: auto; display: flex; }

  .time-col { width: 58px; flex-shrink: 0; border-right: 1px solid var(--bdr-soft); }
  .hour-lbl {
    border-bottom: 1px solid var(--bdr-soft);
    display: flex; align-items: flex-start; justify-content: flex-end;
    padding: 4px 8px 0 0;
    font-size: 11px; font-weight: 500; color: var(--t2);
    flex-shrink: 0;
  }

  .event-col { flex: 1; position: relative; }
  .hour-slot { border-bottom: 1px solid var(--bdr-soft); cursor: pointer; transition: background .12s; }
  .hour-slot:hover { background: var(--acc-bg); }

  .ev-block {
    position: absolute;
    border-radius: 10px; padding: 9px 13px;
    text-align: left; z-index: 1; overflow: hidden;
    cursor: pointer; transition: opacity .12s, filter .12s;
    min-width: 0;
    box-shadow: 0 1px 4px rgba(0,0,0,.2);
  }
  .ev-block:hover { opacity: .9; filter: brightness(1.07); }

  /* Cross-midnight visual cues — remove rounded corners at the clipped edge */
  .ev-block.clipped-start { border-bottom-left-radius: 0; border-bottom-right-radius: 0; }
  .ev-block.clipped-end   { border-top-left-radius: 0;    border-top-right-radius: 0; }

  .ev-title {
    display: block; font-size: var(--fs-sm, 15px); font-weight: 700; margin-bottom: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .ev-block.short { padding: 4px 8px; border-radius: 6px; }
  .ev-block.short .ev-title { font-size: 12px; margin-bottom: 0; }

  .ev-time { display: block; font-size: var(--fs-xs, 13px); opacity: .85; font-weight: 500; }
  .ev-loc  { display: block; font-size: var(--fs-xs, 13px); opacity: .7; margin-top: 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  @media (max-width: 768px) {
    .day-header { padding: 12px 14px 10px; }
    .heading    { font-size: clamp(20px, 6vw, 30px); }
    .ev-block   { padding: 7px 10px; }
  }
</style>
