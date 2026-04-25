<script>
  /**
   * EventPanel.svelte — Add / Edit event panel.
   *
   * [1] Form is only re-initialised when a different event is opened
   *     (guarded by a panel key), so typing is never wiped by store updates.
   * [2] Category→color sync uses a dedicated $effect (mobile-safe).
   * [3] Calendar shown as a custom picker with colour dot.
   */

  import { fly, fade } from 'svelte/transition';
  import {
    panelEvent, closePanel, saveEvent,
    calendars, categories,
  } from '../../lib/stores/index.js';
  import {
    toInputDate, parseInputDate,
    timeToMinutes, minutesToTime,
    describeRecurrence,
  } from '../../lib/utils.js';
  import { HOUR_FORMAT, FIRST_DAY_OF_WEEK } from '../../lib/config.js';

  // ── Form state ──────────────────────────────────────────────
  let form          = $state({});
  let titleError    = $state(false);
  let formCategory  = $state('');
  let lastSyncedCat = $state('');
  let showRecur     = $state(false);
  let showColor     = $state(false);

  // Re-initialise form only when a genuinely different event is opened.
  // Guarded by a panel key so store updates don't wipe in-progress edits.
  let _prevPanelKey = $state(null);

  $effect(() => {
    const p = $panelEvent;
    if (!p) {
      _prevPanelKey = null;
    } else {
      const key = `${p.id}-${(p.startDate ?? '').toString()}`;
      if (key !== _prevPanelKey) {
        _prevPanelKey = key;
        form = {
          ...p,
          startDateStr: toInputDate(p.startDate ?? new Date()),
          endDateStr:   toInputDate(p.endDate   ?? p.startDate ?? new Date()),
          recurrence:   p.recurrence ?? null,
        };
        formCategory  = p.category_id ?? '';
        lastSyncedCat = formCategory;
        titleError    = false;
        showRecur     = !!p.recurrence;
      }
    }
  });

  let isEdit = $derived(!!form.id && form.id !== -1);

  // Category→color sync — two effects so the sync fires reliably on all platforms.
  $effect(() => { form.category_id = formCategory; });
  $effect(() => {
    if (formCategory && formCategory !== lastSyncedCat) {
      const cat = $categories.find(c => c.id === formCategory);
      if (cat) form.color = cat.color;
      lastSyncedCat = formCategory;
    }
  });

  let defaultColor    = $derived($categories.find(c => c.id === formCategory)?.color ?? null);
  let colorOverridden = $derived(defaultColor !== null && form.color !== defaultColor);
  function resetColor() { form.color = defaultColor; }

  // Calendar picker with colour dot
  let selectedCal   = $derived($calendars.find(c => c.id === form.calendar_id) ?? null);
  let showCalPicker = $state(false);

  // Only show categories belonging to the currently selected calendar.
  let calCategories = $derived(
    $categories.filter(c => c.calendar_id === form.calendar_id)
  );

  function pickCalendar(id) {
    form.calendar_id = id;
    showCalPicker    = false;
    // Reset category to the first one of the newly selected calendar
    // so the category list and the colour are always in sync.
    const firstCat = $categories.find(c => c.calendar_id === id);
    formCategory   = firstCat?.id    ?? '';
    form.color     = firstCat?.color ?? form.color;
    lastSyncedCat  = formCategory;
  }
  function onOutsideClick(e) {
    if (!e.target.closest?.('.cal-picker-wrap')) showCalPicker = false;
  }
  $effect(() => {
    if (formCategory && formCategory !== lastSyncedCat) {
      const cat = $categories.find(c => c.id === formCategory);
      if (cat) form.color = cat.color;
      lastSyncedCat = formCategory;
    }
  });

  // Time auto-advance
  function onStartTimeChange() {
    const s = timeToMinutes(form.start ?? '09:00');
    const e = timeToMinutes(form.end   ?? '10:00');
    if (e <= s) form.end = minutesToTime(s + 60);
  }
  function onStartDateChange() {
    if (form.endDateStr < form.startDateStr) form.endDateStr = form.startDateStr;
  }

  // Recurrence helpers
  // Ordered starting from FIRST_DAY_OF_WEEK; jsDay is the JS getDay() value (0=Sun…6=Sat).
  const ALL_DOW_ABBR = ['Su','Mo','Tu','We','Th','Fr','Sa'];
  const DOW_ITEMS = Array.from({ length: 7 }, (_, i) => {
    const jsDay = (FIRST_DAY_OF_WEEK + i) % 7;
    return { label: ALL_DOW_ABBR[jsDay], jsDay };
  });
  function initRecurrence() {
    form.recurrence = { type:'daily', interval:1, days:[], endType:'never', count:5, until: toInputDate(new Date()) };
  }
  function clearRecurrence() { form.recurrence = null; }
  function toggleDay(d) {
    if (!form.recurrence) return;
    const days = form.recurrence.days ?? [];
    form.recurrence = { ...form.recurrence, days: days.includes(d) ? days.filter(x => x !== d) : [...days, d] };
  }
  let recurSummary = $derived(describeRecurrence(form.recurrence));

  // Save
  function handleSave() {
    if (!form.title?.trim()) { titleError = true; return; }
    saveEvent({
      ...form,
      title:     form.title.trim(),
      startDate: parseInputDate(form.startDateStr),
      endDate:   parseInputDate(form.endDateStr),
      recurrence: form.recurrence ?? null,
    });
  }

  // Swatches
  const EXTRAS = ['#e8c4e8','#c4e8e8','#e8e4c4','#b0b0c8'];
  let catColors   = $derived($categories.map(c => c.color));
  let allSwatches = $derived([...new Set([...catColors, ...EXTRAS])]);
</script>

<svelte:window onclick={onOutsideClick} />

{#if $panelEvent}

  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="overlay" onclick={closePanel}
    in:fade={{ duration: 180 }} out:fade={{ duration: 180 }} aria-hidden="true"></div>

  <div
    class="panel"
    role="dialog" aria-modal="true"
    aria-label="{isEdit ? 'Edit event' : 'New event'}"
    in:fly={{ x: 430, duration: 340, easing: t => 1 - Math.pow(1-t,3) }}
    out:fly={{ x: 430, duration: 260 }}
  >
    <!-- Header -->
    <div class="panel-hdr">
      <div class="hdr-accent" style="background:{form.color ?? 'var(--acc)'}"></div>
      <div class="hdr-inner">
        <h2 class="panel-title">{isEdit ? 'Edit event' : 'New event'}</h2>
        <button class="icon-btn" onclick={closePanel} aria-label="Close">✕</button>
      </div>
    </div>

    <div class="panel-body">

      <!-- Title -->
      <div class="field" class:has-error={titleError}>
        <label for="f-title">Title</label>
        <input id="f-title" type="text" bind:value={form.title}
          oninput={() => titleError = false} placeholder="What's happening?" autocomplete="off" />
        {#if titleError}<span class="err-msg" role="alert">Please enter a title.</span>{/if}
      </div>

      <!-- All-day toggle -->
      <label class="toggle-row">
        <input type="checkbox" bind:checked={form.allDay} />
        <span class="toggle-track"><span class="toggle-thumb"></span></span>
        <span class="toggle-lbl">All day</span>
      </label>

      <!-- Dates -->
      <div class="row-2">
        <div class="field">
          <label for="f-sdate">Start date</label>
          <input id="f-sdate" type="date" bind:value={form.startDateStr} onchange={onStartDateChange} />
        </div>
        <div class="field">
          <label for="f-edate">End date</label>
          <input id="f-edate" type="date" bind:value={form.endDateStr} min={form.startDateStr} />
        </div>
      </div>

      <!-- Times (hidden when all-day) -->
      {#if !form.allDay}
        <div class="row-2">
          <div class="field">
            <label for="f-start">Start time</label>
            <input id="f-start" type="time" lang={HOUR_FORMAT === '24' ? 'fr' : 'en-US'} bind:value={form.start} onchange={onStartTimeChange} />
          </div>
          <div class="field">
            <label for="f-end">End time</label>
            <input id="f-end" type="time" lang={HOUR_FORMAT === '24' ? 'fr' : 'en-US'} bind:value={form.end} />
          </div>
        </div>
      {/if}

      <!-- Recurrence -->
      <div class="recur-section">
        <button
          class="recur-toggle"
          type="button"
          aria-expanded={showRecur}
          onclick={() => {
            showRecur = !showRecur;
            if (!showRecur) clearRecurrence();
            else if (!form.recurrence) initRecurrence();
          }}
        >
          <span class="recur-icon" aria-hidden="true">🔁</span>
          <span class="recur-label">{showRecur ? recurSummary : 'Does not repeat'}</span>
          <span class="recur-chevron" class:open={showRecur} aria-hidden="true">▾</span>
        </button>

        {#if showRecur && form.recurrence}
          <div class="recur-body" in:fly={{ y: -8, duration: 180 }}>
            <div class="field">
              <label for="r-type">Repeat</label>
              <select id="r-type" bind:value={form.recurrence.type}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div class="field row-2">
              <div>
                <label for="r-interval">Every</label>
                <input id="r-interval" type="number" bind:value={form.recurrence.interval} min="1" max="99" />
              </div>
              <div style="padding-top:22px; color:var(--t2); font-size:var(--fs-sm)">
                {form.recurrence.type === 'daily' ? 'days' : form.recurrence.type === 'weekly' ? 'weeks' : form.recurrence.type === 'monthly' ? 'months' : 'years'}
              </div>
            </div>
            {#if form.recurrence.type === 'weekly'}
              <div class="field">
                <label>On days</label>
                <div class="dow-row">
                  {#each DOW_ITEMS as { label, jsDay }}
                    <button type="button" class="dow-btn"
                      class:on={form.recurrence.days?.includes(jsDay)}
                      onclick={() => toggleDay(jsDay)}
                      aria-pressed={form.recurrence.days?.includes(jsDay)}>{label}</button>
                  {/each}
                </div>
              </div>
            {/if}
            <div class="field">
              <label for="r-end">Ends</label>
              <select id="r-end" bind:value={form.recurrence.endType}>
                <option value="never">Never</option>
                <option value="count">After N occurrences</option>
                <option value="until">On date</option>
              </select>
            </div>
            {#if form.recurrence.endType === 'count'}
              <div class="field">
                <label for="r-count">Occurrences</label>
                <input id="r-count" type="number" bind:value={form.recurrence.count} min="1" max="999" />
              </div>
            {/if}
            {#if form.recurrence.endType === 'until'}
              <div class="field">
                <label for="r-until">Until</label>
                <input id="r-until" type="date" bind:value={form.recurrence.until} min={form.startDateStr} />
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Calendar picker -->
      <div class="field">
        <label>Calendar</label>
        <div class="cal-picker-wrap">
          <button class="cal-trigger" type="button"
            onclick={() => showCalPicker = !showCalPicker}
            aria-haspopup="listbox" aria-expanded={showCalPicker}>
            {#if selectedCal}
              <span class="cal-dot" style="background:{selectedCal.color}"></span>
              <span class="cal-name">{selectedCal.title}</span>
            {:else}
              <span class="cal-name placeholder">Select calendar…</span>
            {/if}
            <span class="cal-chevron" class:open={showCalPicker}>▾</span>
          </button>
          {#if showCalPicker}
            <ul class="cal-dropdown" role="listbox" in:fly={{ y: -6, duration: 150 }}>
              {#each $calendars as cal (cal.id)}
                <li>
                  <button class="cal-option" class:selected={form.calendar_id === cal.id}
                    role="option" aria-selected={form.calendar_id === cal.id}
                    type="button" onclick={() => pickCalendar(cal.id)}>
                    <span class="cal-dot" style="background:{cal.color}"></span>
                    <span>{cal.title}</span>
                    {#if form.calendar_id === cal.id}<span class="cal-check">✓</span>{/if}
                  </button>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </div>

      <!-- Category — filtered to the selected calendar -->
      <div class="field">
        <label for="f-cat">Category</label>
        <select id="f-cat" bind:value={formCategory}>
          {#if calCategories.length === 0}
            <option value="">No categories for this calendar</option>
          {:else}
            {#each calCategories as cat (cat.id)}
              <option value={cat.id}>{cat.icon}  {cat.label}</option>
            {/each}
          {/if}
        </select>
      </div>

      <!-- Location -->
      <div class="field">
        <label for="f-loc">Location</label>
        <input id="f-loc" type="text" bind:value={form.adresse} placeholder="Add a location" autocomplete="off" />
      </div>

      <!-- Notes -->
      <div class="field">
        <label for="f-notes">Notes</label>
        <textarea id="f-notes" bind:value={form.description} placeholder="Add notes…"></textarea>
      </div>

      <!-- Colour picker -->
      <div class="field">
        <div class="color-header">
          <label>Colour</label>
          <button class="color-toggle" type="button" onclick={() => showColor = !showColor}>
            <span class="preview-dot-sm" style="background:{form.color}"></span>
            {showColor ? 'Hide' : 'Custom colour'}
          </button>
        </div>
        {#if showColor}
          <div class="swatches" role="group" aria-label="Event colour">
            {#each allSwatches as hex (hex)}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <div class="swatch" class:selected={form.color === hex} class:is-default={hex === defaultColor}
                style="background:{hex}" role="radio" aria-checked={form.color === hex} tabindex="0"
                onclick={() => form.color = hex}
                onkeydown={e => e.key === 'Enter' && (form.color = hex)}>
                {#if hex === defaultColor}<span class="def-marker" aria-hidden="true"></span>{/if}
              </div>
            {/each}
            <label class="custom-swatch" title="Custom colour">
              <input type="color" value={form.color} oninput={e => form.color = e.target.value} />
              <span aria-hidden="true">🎨</span>
            </label>
          </div>
          <div class="color-preview">
            <span class="preview-dot" style="background:{form.color}"></span>
            <span class="preview-hex">{form.color}</span>
            {#if colorOverridden}
              <button class="reset-color" type="button" onclick={resetColor}>↺ Reset to category</button>
            {/if}
          </div>
        {/if}
      </div>

    </div>

    <!-- Footer -->
    <div class="panel-ftr">
      <button class="btn-cancel" type="button" onclick={closePanel}>Cancel</button>
      <button class="btn-save"   type="button" onclick={handleSave}>
        {isEdit ? 'Update' : 'Save event'}
      </button>
    </div>

  </div>

{/if}

<style>
  .overlay { position:fixed; inset:0; background:rgba(0,0,0,.52); backdrop-filter:blur(4px); z-index:49; }

  .panel {
    position:fixed; top:0; right:0; bottom:0; width:min(440px,100vw);
    background:var(--bg-surf); border-left:1px solid var(--bdr);
    z-index:50; display:flex; flex-direction:column;
    box-shadow:-6px 0 40px rgba(0,0,0,.45); overflow:hidden;
  }
  @media (max-width:768px) {
    .panel { top:auto; left:0; right:0; bottom:0; width:100%; height:94dvh;
      border-left:none; border-top:1px solid var(--bdr);
      border-radius:22px 22px 0 0; transform:translateX(0)!important; }
  }

  .panel-hdr { flex-shrink:0; border-bottom:1px solid var(--bdr-soft); overflow:hidden; }
  .hdr-accent { height:4px; transition:background .3s; }
  .hdr-inner  { padding:14px 22px 12px; display:flex; align-items:center; justify-content:space-between; }
  .panel-title { font-family:var(--f-display); font-size:var(--fs-xl,24px); font-weight:400; letter-spacing:.02em; }

  .icon-btn {
    width:32px; height:32px; border-radius:var(--r-s);
    color:var(--t3); font-size:15px;
    display:flex; align-items:center; justify-content:center;
    transition:color .13s, background .13s;
  }
  .icon-btn:hover { color:var(--acc); background:var(--acc-bg); }

  .panel-body { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:14px; }

  .field { display:flex; flex-direction:column; gap:6px; }
  .field.has-error input { border-color:#f47070; }
  label { font-size:11px; font-weight:500; color:var(--t2); text-transform:uppercase; letter-spacing:.07em; }
  .err-msg { font-size:var(--fs-xs,13px); color:#f47070; }
  .row-2   { display:grid; grid-template-columns:1fr 1fr; gap:12px; }

  /* All-day toggle */
  .toggle-row { display:flex; align-items:center; gap:10px; cursor:pointer; }
  .toggle-row input[type="checkbox"] { display:none; }
  .toggle-track {
    width:36px; height:20px; border-radius:10px;
    background:var(--bg-raised); border:1px solid var(--bdr); position:relative;
    transition:background .18s, border-color .18s; flex-shrink:0;
  }
  .toggle-row input:checked ~ .toggle-track { background:var(--acc-dim); border-color:var(--acc-dim); }
  .toggle-thumb {
    position:absolute; top:2px; left:2px; width:14px; height:14px; border-radius:50%;
    background:var(--t3); transition:transform .18s, background .18s;
  }
  .toggle-row input:checked ~ .toggle-track .toggle-thumb { transform:translateX(16px); background:#1a0812; }
  .toggle-lbl { font-size:var(--fs-sm,15px); color:var(--t2); }

  /* Recurrence — no overflow:hidden so expanded body is never clipped */
  .recur-section {
    border: 1px solid var(--bdr-soft);
    border-radius: var(--r-m);
    /* NOTE: overflow:hidden was removed — it was clipping the expanded recur-body
       during the fly() animation and cutting off content on small screens. */
  }
  .recur-toggle {
    width:100%; padding:11px 14px; display:flex; align-items:center; gap:10px;
    background:var(--bg-card); text-align:left; transition:background .12s;
    border-radius: var(--r-m); /* always round all corners */
  }
  /* When expanded, only round the top; the body will round the bottom */
  .recur-section:has(.recur-body) .recur-toggle {
    border-radius: var(--r-m) var(--r-m) 0 0;
  }
  .recur-toggle:hover { background:var(--bg-raised); }
  .recur-icon  { font-size:14px; flex-shrink:0; }
  .recur-label { flex:1; font-size:var(--fs-sm,15px); color:var(--t2); }
  .recur-chevron      { font-size:11px; color:var(--t3); transition:transform .14s; }
  .recur-chevron.open { transform:rotate(180deg); }
  .recur-body {
    padding:14px; border-top:1px solid var(--bdr-soft);
    display:flex; flex-direction:column; gap:12px; background:var(--bg-surf);
    border-radius: 0 0 var(--r-m) var(--r-m);
    border: 1px solid var(--bdr-soft);
    border-top: none;
    /* Ensure all options are visible without clipping */
    overflow: visible;
  }
  .dow-row { display:flex; gap:5px; flex-wrap:wrap; }
  .dow-btn {
    width:32px; height:32px; border-radius:50%;
    font-size:var(--fs-xs,13px); font-weight:500; color:var(--t2);
    border:1.5px solid var(--bdr);
    display:flex; align-items:center; justify-content:center; transition:all .12s;
  }
  .dow-btn.on { background:var(--acc); border-color:var(--acc); color:#1a0812; font-weight:700; }

  /* Calendar picker */
  .cal-picker-wrap { position:relative; }
  .cal-trigger {
    width:100%; padding:10px 14px;
    background:var(--bg-raised); border:1px solid var(--bdr); border-radius:var(--r-s);
    color:var(--t1); font-size:var(--fs-sm,15px);
    display:flex; align-items:center; gap:10px; cursor:pointer; text-align:left;
    transition:border-color .16s, box-shadow .16s;
  }
  .cal-trigger:hover { border-color:var(--acc-dim); }
  .cal-trigger:focus { border-color:var(--acc-dim); box-shadow:0 0 0 3px rgba(244,184,200,.07); outline:none; }
  .cal-dot  { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  .cal-name { flex:1; }
  .cal-name.placeholder { color:var(--t3); }
  .cal-chevron { font-size:11px; color:var(--t3); transition:transform .14s; }
  .cal-chevron.open { transform:rotate(180deg); }
  .cal-dropdown {
    position:absolute; top:calc(100% + 4px); left:0; right:0;
    background:var(--bg-card); border:1px solid var(--bdr); border-radius:var(--r-s);
    z-index:10; list-style:none; box-shadow:0 8px 24px rgba(0,0,0,.4); overflow:hidden;
  }
  .cal-option {
    width:100%; padding:10px 14px; display:flex; align-items:center; gap:10px;
    font-size:var(--fs-sm,15px); color:var(--t2); cursor:pointer; transition:background .12s; text-align:left;
  }
  .cal-option:hover    { background:var(--acc-bg); color:var(--t1); }
  .cal-option.selected { color:var(--t1); }
  .cal-check { margin-left:auto; font-size:11px; color:var(--acc); }

  /* Colour picker */
  .color-header { display:flex; align-items:center; justify-content:space-between; }
  .color-toggle { display:flex; align-items:center; gap:6px; font-size:var(--fs-xs,13px); color:var(--acc-dim); text-decoration:underline; text-underline-offset:2px; }
  .color-toggle:hover { color:var(--acc); }
  .preview-dot-sm { display:inline-block; width:12px; height:12px; border-radius:50%; flex-shrink:0; }
  .reset-color  { font-size:var(--fs-xs,13px); color:var(--acc-dim); text-decoration:underline; text-underline-offset:2px; }
  .reset-color:hover { color:var(--acc); }
  .color-hint   { font-size:var(--fs-xs,13px); color:var(--t3); font-style:italic; }
  .swatches { display:flex; gap:8px; flex-wrap:wrap; padding:2px 0; align-items:center; }
  .swatch {
    width:28px; height:28px; border-radius:50%; cursor:pointer;
    border:2.5px solid transparent; position:relative;
    transition:transform .13s, border-color .13s, box-shadow .13s;
  }
  .swatch:hover    { transform:scale(1.14); }
  .swatch.selected { border-color:var(--t1); box-shadow:0 0 0 3px rgba(240,234,240,.15); transform:scale(1.06); }
  .swatch.is-default .def-marker {
    position:absolute; bottom:-1px; right:-1px; width:7px; height:7px;
    background:var(--t1); border-radius:1px; transform:rotate(45deg);
  }
  .custom-swatch {
    width:28px; height:28px; border-radius:50%; cursor:pointer; overflow:hidden;
    border:1.5px dashed var(--bdr); display:flex; align-items:center; justify-content:center;
    transition:border-color .13s; position:relative;
  }
  .custom-swatch:hover { border-color:var(--acc-dim); }
  .custom-swatch input[type="color"] { position:absolute; opacity:0; width:0; height:0; }
  .color-preview { display:flex; align-items:center; gap:8px; margin-top:4px; }
  .preview-dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; transition:background .2s; }
  .preview-hex { font-family:var(--f-mono); font-size:var(--fs-xs,13px); color:var(--t3); letter-spacing:.04em; }

  /* Footer */
  .panel-ftr { padding:14px 20px; border-top:1px solid var(--bdr-soft); display:flex; gap:10px; flex-shrink:0; }
  .btn-cancel {
    flex:1; padding:12px; border-radius:var(--r-s);
    border:1px solid var(--bdr); color:var(--t2); font-size:var(--fs-sm,15px); transition:all .16s;
  }
  .btn-cancel:hover { border-color:var(--acc-dim); color:var(--acc); }
  .btn-save {
    flex:2; padding:12px; border-radius:var(--r-s);
    background:linear-gradient(135deg, var(--acc), var(--acc-dim));
    color:#1a0812; font-weight:600; font-size:var(--fs-sm,15px);
    box-shadow:0 2px 12px var(--acc-glow); transition:opacity .16s, transform .13s;
  }
  .btn-save:hover  { opacity:.9; transform:translateY(-1px); }
  .btn-save:active { transform:translateY(0); }
</style>
