<script>
  /**
   * EventModal.svelte — Single event detail view (read-only).
   *
   * Shows: multi-day date range, all-day badge, recurrence summary,
   * location, calendar, description, and edit/duplicate/delete actions.
   */

  import { fly, fade } from 'svelte/transition';
  import {
    modalEventId, modalOccurrenceDate, events, calendars, categories,
    openEditPanel, openDuplicatePanel, deleteEvent, excludeOccurrence,
  } from '../../lib/stores/index.js';
  import {
    MONTH_ABBR, DAY_NAMES, formatTime,
    sameDay, describeRecurrence,
  } from '../../lib/utils.js';

  // ── Reactive lookups ────────────────────────────────────────
  let ev       = $derived($modalEventId != null ? $events.find(e => e.id === $modalEventId) : null);
  let cal      = $derived(ev ? $calendars .find(c => c.id === ev.calendar_id) : null);
  let cat      = $derived(ev ? $categories.find(c => c.id === ev.category_id) : null);
  let catColor = $derived(cat ? cat.color : (ev?.color ?? '#888'));

  // ── Date display (handles new startDate/endDate model) ──────
  let dateStr  = $derived(ev ? buildDateStr(ev) : '');
  let recurStr = $derived(ev?.recurrence ? describeRecurrence(ev.recurrence) : null);

  function buildDateStr(ev) {
    const s = ev.startDate instanceof Date ? ev.startDate : new Date(ev.startDate);
    const e = ev.endDate   instanceof Date ? ev.endDate   : new Date(ev.endDate ?? ev.startDate);

    const sLabel = `${DAY_NAMES[s.getDay()]}, ${MONTH_ABBR[s.getMonth()]} ${s.getDate()}`;

    if (ev.allDay) {
      if (sameDay(s, e)) return `${sLabel} · All day`;
      const eLabel = `${DAY_NAMES[e.getDay()]}, ${MONTH_ABBR[e.getMonth()]} ${e.getDate()}`;
      return `${sLabel} – ${eLabel} · All day`;
    }

    // Timed event
    const timeRange = ev.start && ev.end
      ? `${formatTime(ev.start)} – ${formatTime(ev.end)}`
      : '';

    if (sameDay(s, e)) return `${sLabel}${timeRange ? ' · ' + timeRange : ''}`;

    const eLabel = `${DAY_NAMES[e.getDay()]}, ${MONTH_ABBR[e.getMonth()]} ${e.getDate()}`;
    return `${sLabel} – ${eLabel}${timeRange ? ' · ' + timeRange : ''}`;
  }

  let canEdit = $derived(cal ? (cal.right === 'write' || cal.right === 'admin' || !cal.right) : true);

  // Recurrence delete choice popup
  let showRecurChoice = $state(false);

  function close() { $modalEventId = null; $modalOccurrenceDate = null; showRecurChoice = false; }

  function onBackdropClick(e) {
    if (e.target === e.currentTarget) close();
  }

  function onEdit() {
    const id = ev.id;
    close();
    openEditPanel(id);
  }

  function onDuplicate() {
    const id = ev.id;
    close();
    openDuplicatePanel(id);
  }

  function onDelete() {
    if (ev.recurrence_id || ev.recurrence) {
      showRecurChoice = true;
    } else {
      deleteEvent(ev.id);
    }
  }

  function onDeleteAll() {
    deleteEvent(ev.id);
    showRecurChoice = false;
  }

  function onDeleteOccurrence() {
    const occDate = $modalOccurrenceDate ?? ev.startDate;
    excludeOccurrence(ev.id, occDate instanceof Date ? occDate : new Date(occDate));
    showRecurChoice = false;
  }
</script>

{#if ev}

  <!-- Backdrop -->
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="backdrop"
    onclick={onBackdropClick}
    in:fade={{ duration: 200 }}
    out:fade={{ duration: 180 }}
    aria-hidden="true"
  ></div>

  <!-- Modal -->
  <div
    class="modal"
    role="dialog"
    aria-modal="true"
    aria-label={ev.title}
    in:fly={{ y: 28, duration: 300, easing: t => 1 - Math.pow(1-t, 3) }}
    out:fly={{ y: 20, duration: 200 }}
  >
    <!-- Colour accent strip -->
    <div class="banner" style="background:{catColor}"></div>

    <div class="body">

      <!-- Close -->
      <button class="close-btn" onclick={close} aria-label="Close">✕</button>

      <!-- Category tag -->
      <div class="ev-cat">
        <span class="cat-dot" style="background:{catColor}"></span>
        <span class="cat-label" style="color:{catColor}">
          {cat ? cat.icon + ' ' + cat.label : '—'}
        </span>
        {#if ev.allDay}
          <span class="badge">All day</span>
        {/if}
        {#if cal && cal.right === 'read'}
          <span class="badge muted">Read only</span>
        {/if}
      </div>

      <!-- Title -->
      <h2 class="ev-title">{ev.title}</h2>

      <!-- Date / time (uses new model) -->
      <div class="detail-row">
        <span class="ico" aria-hidden="true">🕐</span>
        <span>{dateStr}</span>
      </div>

      <!-- Recurrence summary -->
      {#if recurStr}
        <div class="detail-row">
          <span class="ico" aria-hidden="true">🔁</span>
          <span>{recurStr}</span>
        </div>
      {/if}

      <!-- Location -->
      {#if ev.adresse}
        <div class="detail-row">
          <span class="ico" aria-hidden="true">📍</span>
          <span>{ev.adresse}</span>
        </div>
      {/if}

      <!-- Calendar -->
      {#if cal}
        <div class="detail-row">
          <span class="ico" aria-hidden="true">📅</span>
          <span style="color:{cal.color}">{cal.title}</span>
        </div>
      {/if}

      <!-- Description -->
      {#if ev.description}
        <p class="ev-desc">{ev.description}</p>
      {/if}

      <!-- Actions -->
      {#if canEdit}
        <div class="actions">
          <button class="btn-edit"      onclick={onEdit}>Edit</button>
          <button class="btn-duplicate" onclick={onDuplicate} title="Duplicate this event">⎘</button>
          <button class="btn-delete"    onclick={onDelete}>Delete</button>
        </div>
      {:else}
        <div class="actions">
          <button class="btn-duplicate" onclick={onDuplicate} title="Duplicate this event">⎘ Duplicate</button>
          <button class="btn-ghost"     onclick={close}>Close</button>
        </div>
      {/if}

      <!-- Recurrence delete choice -->
      {#if showRecurChoice}
        <div class="recur-choice" in:fly={{ y: 8, duration: 180 }}>
          <p class="recur-choice-label">Delete recurring event</p>
          <div class="recur-choice-btns">
            <button class="btn-choice-occ" onclick={onDeleteOccurrence}>
              This occurrence only
            </button>
            <button class="btn-choice-all" onclick={onDeleteAll}>
              All occurrences
            </button>
          </div>
          <button class="btn-choice-cancel" onclick={() => showRecurChoice = false}>Cancel</button>
        </div>
      {/if}

    </div>
  </div>

{/if}

<style>
  /* ── Backdrop ───────────────────────────────────────────── */
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.62); backdrop-filter: blur(6px); z-index: 59;
  }

  /* ── Modal — desktop centred ───────────────────────────── */
  .modal {
    position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: min(500px, calc(100vw - 32px));
    background: var(--bg-surf); border: 1px solid var(--bdr);
    border-radius: var(--r-xl); z-index: 60;
    box-shadow: var(--shadow-card), var(--shadow-glow); overflow: hidden;
  }

  /* Mobile: bottom sheet */
  @media (max-width: 768px) {
    .modal {
      top: auto; left: 0; right: 0; bottom: 0; transform: none;
      width: 100%; border-radius: var(--r-xl) var(--r-xl) 0 0;
      max-height: 90dvh; overflow-y: auto;
    }
  }

  .banner { height: 6px; flex-shrink: 0; }

  /* ── Body ───────────────────────────────────────────────── */
  .body { padding: 24px 28px 28px; position: relative; }

  .close-btn {
    position: absolute; top: 14px; right: 16px;
    width: 32px; height: 32px; border-radius: var(--r-s);
    color: var(--t3); font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    transition: color .14s, background .14s; z-index: 2;
  }
  .close-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Category row ───────────────────────────────────────── */
  .ev-cat {
    display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .cat-dot   { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .cat-label { font-size: var(--fs-xs, 13px); font-weight: 600; text-transform: uppercase; letter-spacing: .10em; }

  .badge {
    font-size: 10px; color: var(--t3);
    border: 1px solid var(--bdr); border-radius: 20px;
    padding: 1px 8px; letter-spacing: .05em;
  }
  .badge.muted { color: var(--t3); }

  /* ── Title ──────────────────────────────────────────────── */
  .ev-title {
    font-family: var(--f-display);
    font-size: clamp(var(--fs-xl, 24px), 6vw, 34px);
    font-weight: 400; color: var(--t1);
    letter-spacing: .02em; line-height: 1.2; margin-bottom: 20px;
  }

  /* ── Detail rows ────────────────────────────────────────── */
  .detail-row {
    display: flex; align-items: flex-start; gap: 11px;
    color: var(--t2); font-size: var(--fs-sm, 15px);
    margin-bottom: 11px; line-height: 1.5;
  }
  .ico { font-size: 16px; flex-shrink: 0; margin-top: 1px; }

  /* ── Description ────────────────────────────────────────── */
  .ev-desc {
    font-size: var(--fs-sm, 15px); color: var(--t3);
    line-height: 1.65; margin-top: 14px; padding-top: 14px;
    border-top: 1px solid var(--bdr-soft);
  }

  /* ── Actions ────────────────────────────────────────────── */
  .actions {
    display: flex; gap: 10px;
    margin-top: 24px; padding-top: 18px;
    border-top: 1px solid var(--bdr-soft);
  }

  .btn-edit {
    flex: 2; padding: 12px; border-radius: var(--r-s);
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-weight: 600; font-size: var(--fs-sm, 15px);
    box-shadow: 0 2px 12px var(--acc-glow); transition: opacity .16s, transform .13s;
  }
  .btn-edit:hover  { opacity: .9; transform: translateY(-1px); }
  .btn-edit:active { transform: translateY(0); }

  .btn-duplicate {
    flex: 1; padding: 12px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2);
    font-size: var(--fs-sm, 15px); transition: all .16s;
  }
  .btn-duplicate:hover { border-color: var(--acc-dim); color: var(--acc); background: var(--acc-bg); }

  .btn-delete {
    flex: 1; padding: 12px; border-radius: var(--r-s);
    border: 1px solid rgba(244,100,100,.22);
    color: #f47070; font-size: var(--fs-sm, 15px); transition: all .16s;
  }
  .btn-delete:hover { background: rgba(244,100,100,.08); border-color: rgba(244,100,100,.4); }

  .btn-ghost {
    flex: 1; padding: 12px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2);
    font-size: var(--fs-sm, 15px); transition: all .16s;
  }
  .btn-ghost:hover { border-color: var(--acc-dim); color: var(--acc); }

  /* ── Recurrence delete choice ───────────────────────────── */
  .recur-choice {
    margin-top: 12px; padding: 16px;
    background: var(--bg-raised); border: 1px solid var(--bdr);
    border-radius: var(--r-m); display: flex; flex-direction: column; gap: 10px;
  }
  .recur-choice-label {
    font-size: var(--fs-xs, 13px); font-weight: 600;
    color: var(--t2); text-transform: uppercase; letter-spacing: .07em;
  }
  .recur-choice-btns { display: flex; gap: 8px; }
  .btn-choice-occ {
    flex: 1; padding: 10px 12px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t1);
    font-size: var(--fs-sm, 15px); transition: all .14s;
  }
  .btn-choice-occ:hover { border-color: var(--acc-dim); color: var(--acc); background: var(--acc-bg); }
  .btn-choice-all {
    flex: 1; padding: 10px 12px; border-radius: var(--r-s);
    border: 1px solid rgba(244,100,100,.22);
    color: #f47070; font-size: var(--fs-sm, 15px); transition: all .14s;
  }
  .btn-choice-all:hover { background: rgba(244,100,100,.08); border-color: rgba(244,100,100,.4); }
  .btn-choice-cancel {
    align-self: center; font-size: var(--fs-xs, 13px); color: var(--t3);
    text-decoration: underline; text-underline-offset: 2px; transition: color .13s;
  }
  .btn-choice-cancel:hover { color: var(--t2); }
</style>
