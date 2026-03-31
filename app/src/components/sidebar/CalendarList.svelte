<script>
  /**
   * CalendarList.svelte — Left-sidebar section: calendar filter list.
   *
   * Features:
   *  • Toggle calendar visibility (filter) via checkbox rows
   *  • Gear icon → CalendarSettings modal (admin only)
   *  • "＋ New calendar" button expands an inline create form
   *  • Inline form: name + colour picker → createCalendar()
   */

  import { fly } from 'svelte/transition';
  import {
    calendars, calSettingsId,
    toggleCalendar, createCalendar,
  } from '../../lib/stores/index.js';

  // ── Colour palette for new calendars ──────────────────────
  const PALETTE = [
    '#f4b8c8', '#b8c9f4', '#b8f4d4', '#f4d8b8',
    '#d8b8f4', '#f4f0b8', '#b8e8f4', '#f4b8e8',
  ];

  // ── Inline create form state ───────────────────────────────
  let creating   = false;  // whether the inline form is expanded
  let newName    = '';
  let newColor   = PALETTE[0];
  let saving     = false;
  let nameError  = false;

  function openCreate() {
    creating  = true;
    newName   = '';
    newColor  = PALETTE[0];
    nameError = false;
  }

  function cancelCreate() { creating = false; }

  async function submitCreate() {
    if (!newName.trim()) { nameError = true; return; }
    saving = true;
    try {
      await createCalendar({ name: newName.trim(), color: newColor });
      creating = false;
    } finally {
      saving = false;
    }
  }

  // Submit on Enter in the name field
  function onNameKeydown(e) {
    if (e.key === 'Enter') submitCreate();
    if (e.key === 'Escape') cancelCreate();
  }
</script>

<section class="cal-list">

  <!-- Section header -->
  <div class="sec-hdr">
    <h3 class="sec-title">My Calendars</h3>
    {#if !creating}
      <button
        class="hdr-btn"
        on:click={openCreate}
        aria-label="Create new calendar"
        title="New calendar"
      >＋</button>
    {/if}
  </div>

  <!-- Calendar rows -->
  {#each $calendars as cal (cal.id)}
    <div class="cal-row">
      <button
        class="row-toggle"
        on:click={() => toggleCalendar(cal.id)}
        aria-pressed={cal.on}
        aria-label="{cal.name}, {cal.on ? 'visible' : 'hidden'}"
      >
        <span class="dot" style="background:{cal.color}"></span>
        <span class="row-label" class:off={!cal.on}>{cal.name}</span>
        <span class="chk" class:on={cal.on} aria-hidden="true">
          {#if cal.on}✓{/if}
        </span>
      </button>

      {#if cal.role === 'admin'}
        <button
          class="gear-btn"
          on:click={() => $calSettingsId = cal.id}
          aria-label="Edit {cal.name}"
          title="Edit calendar"
        >✎</button>
      {/if}
    </div>
  {/each}

  <!-- Inline create form -->
  {#if creating}
    <div
      class="create-form"
      in:fly={{ y: -8, duration: 200 }}
    >
      <!-- Name field -->
      <div class="cf-field" class:err={nameError}>
        <input
          type="text"
          bind:value={newName}
          on:input={() => nameError = false}
          on:keydown={onNameKeydown}
          placeholder="Calendar name"
          autocomplete="off"
          autofocus
        />
        {#if nameError}
          <span class="err-msg">Enter a name</span>
        {/if}
      </div>

      <!-- Colour swatches -->
      <div class="cf-swatches" role="group" aria-label="Calendar colour">
        {#each PALETTE as hex}
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <div
            class="cf-swatch"
            class:sel={newColor === hex}
            style="background:{hex}"
            role="radio"
            aria-checked={newColor === hex}
            tabindex="0"
            on:click={() => newColor = hex}
            on:keydown={e => e.key === 'Enter' && (newColor = hex)}
          ></div>
        {/each}
      </div>

      <!-- Actions -->
      <div class="cf-actions">
        <button class="cf-save" on:click={submitCreate} disabled={saving}>
          {saving ? '…' : 'Create'}
        </button>
        <button class="cf-cancel" on:click={cancelCreate}>Cancel</button>
      </div>
    </div>
  {/if}

</section>

<style>
  .cal-list { padding: 0; }

  /* ── Section header ─────────────────────────────────────── */
  .sec-hdr {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 2px 0 8px; margin-bottom: 5px;
  }
  .sec-title {
    font-size: var(--fs-xs, 13px); font-weight: 500;
    color: var(--t3); text-transform: uppercase; letter-spacing: .10em;
  }
  .hdr-btn {
    width: 22px; height: 22px; border-radius: 5px;
    font-size: 16px; color: var(--t3);
    display: flex; align-items: center; justify-content: center;
    transition: color .13s, background .13s;
  }
  .hdr-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Calendar row ───────────────────────────────────────── */
  .cal-row {
    display: flex; align-items: center;
    border-radius: var(--r-s);
    transition: background .13s;
  }
  .cal-row:hover { background: var(--acc-bg); }

  .row-toggle {
    display: flex; align-items: center; gap: 10px;
    flex: 1; padding: 7px 8px; border-radius: var(--r-s);
    text-align: left; min-width: 0;
  }
  .cal-row .row-toggle:hover { background: none; }

  .dot {
    width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
  }
  .row-label {
    font-size: var(--fs-sm, 15px); color: var(--t2);
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    transition: color .13s;
  }
  .row-label.off { color: var(--t3); }

  .chk {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1.5px solid var(--bdr);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; flex-shrink: 0;
    color: transparent;
    transition: background .13s, border-color .13s;
  }
  .chk.on { background: var(--acc); border-color: var(--acc); color: #1a0812; }

  .gear-btn {
    width: 28px; height: 28px; border-radius: 6px;
    font-size: 13px; color: var(--t3); flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity .13s, color .13s, background .13s;
  }
  .cal-row:hover .gear-btn { opacity: 1; }
  .gear-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Inline create form ─────────────────────────────────── */
  .create-form {
    margin-top: 6px;
    background: var(--bg-card);
    border: 1px solid var(--bdr);
    border-radius: var(--r-m);
    padding: 12px;
    display: flex; flex-direction: column; gap: 10px;
  }

  .cf-field { display: flex; flex-direction: column; gap: 4px; }
  .cf-field.err input { border-color: #f47070; }
  .err-msg { font-size: var(--fs-xs, 13px); color: #f47070; }

  .cf-swatches {
    display: flex; gap: 7px; flex-wrap: wrap;
  }
  .cf-swatch {
    width: 22px; height: 22px; border-radius: 50%;
    cursor: pointer; border: 2px solid transparent;
    transition: transform .13s, border-color .13s;
  }
  .cf-swatch:hover { transform: scale(1.15); }
  .cf-swatch.sel {
    border-color: var(--t1);
    box-shadow: 0 0 0 2px rgba(240,234,240,.2);
    transform: scale(1.06);
  }

  .cf-actions { display: flex; gap: 8px; }
  .cf-save {
    flex: 2; padding: 8px; border-radius: var(--r-s);
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-weight: 600; font-size: var(--fs-xs, 13px);
    transition: opacity .15s;
  }
  .cf-save:hover:not(:disabled) { opacity: .88; }
  .cf-save:disabled { opacity: .4; cursor: not-allowed; }

  .cf-cancel {
    flex: 1; padding: 8px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2);
    font-size: var(--fs-xs, 13px); transition: all .13s;
  }
  .cf-cancel:hover { border-color: var(--acc-dim); color: var(--acc); }
</style>
