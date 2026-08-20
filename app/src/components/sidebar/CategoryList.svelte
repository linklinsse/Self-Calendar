<script>
  /**
   * CategoryList.svelte — Left-sidebar section: category filter list.
   *
   * Categories are grouped under their parent calendar so the
   * relationship is visually obvious. Each group shows a coloured
   * calendar dot + name as a header before its categories.
   *
   * Only shows categories whose calendar is currently active (toggled on).
   * Uses the `visibleCategories` derived store from categories.js.
   */

  import {
    visibleCategories, catEditorId,
    toggleCategory, calendars,
  } from '../../lib/stores/index.js';

  /** Build an ordered list of { calendar, cats[] } groups from visible cats. */
  let groups = $derived((() => {
    const calMap = new Map($calendars.map(c => [c.id, c]));
    const byCalendar = new Map();

    for (const cat of $visibleCategories) {
      if (!byCalendar.has(cat.calendar_id)) {
        byCalendar.set(cat.calendar_id, { calendar: calMap.get(cat.calendar_id), cats: [] });
      }
      byCalendar.get(cat.calendar_id).cats.push(cat);
    }

    return [...byCalendar.values()];
  })());
</script>

<section class="cat-list">

  <!-- Section header -->
  <div class="sec-hdr">
    <h3 class="sec-title">Categories</h3>
    <button
      class="hdr-btn"
      onclick={() => $catEditorId = -1}
      aria-label="Create new category"
      title="New category"
    >＋</button>
  </div>

  <!-- Groups: one per active calendar -->
  {#each groups as group (group.calendar?.id ?? 'unknown')}
    <!-- Calendar group header -->
    <div class="cal-group-hdr">
      <span
        class="cal-dot"
        style="background: {group.calendar?.color ?? '#888'}"
        aria-hidden="true"
      ></span>
      <span class="cal-group-name">{group.calendar?.title ?? 'Unknown'}</span>
    </div>

    <!-- Category rows for this calendar -->
    {#each group.cats as cat (cat.id)}
      <div class="cat-row-wrap">
        <button
          class="cat-row"
          class:off={!cat.on}
          onclick={() => toggleCategory(cat.id)}
          aria-pressed={cat.on}
          aria-label="{cat.label}, {cat.on ? 'visible' : 'hidden'}"
        >
          <span class="cat-icon" aria-hidden="true">{cat.icon}</span>
          <span class="row-label">{cat.label}</span>
          <span
            class="cat-pip"
            style="background:{cat.color}"
            class:pip-off={!cat.on}
            aria-hidden="true"
          ></span>
        </button>

        <button
          class="edit-btn"
          onclick={() => $catEditorId = cat.id}
          aria-label="Edit {cat.label}"
          title="Edit category"
        >✎</button>
      </div>
    {/each}
  {/each}

  {#if $visibleCategories.length === 0}
    <p class="empty-hint">No categories for active calendars.</p>
  {/if}

</section>

<style>
  .cat-list { padding: 0; }

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

  /* ── Calendar group header ──────────────────────────────── */
  .cal-group-hdr {
    display: flex; align-items: center; gap: 6px;
    padding: 8px 8px 3px;
    margin-top: 4px;
  }
  .cal-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  }
  .cal-group-name {
    font-size: var(--fs-xs, 12px); font-weight: 600;
    color: var(--t2); text-transform: uppercase; letter-spacing: .08em;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

  /* ── Category row wrapper ───────────────────────────────── */
  .cat-row-wrap {
    display: flex; align-items: center;
    border-radius: 20px;
    transition: background .13s;
    padding-left: 14px; /* indent under calendar group */
  }
  .cat-row-wrap:hover { background: var(--acc-bg); }

  /* ── Category row button ────────────────────────────────── */
  .cat-row {
    display: flex; align-items: center; gap: 10px;
    flex: 1; padding: 6px 8px; border-radius: 20px;
    text-align: left; min-width: 0;
    transition: background .13s;
  }
  .cat-row-wrap .cat-row:hover { background: none; }

  .cat-icon { font-size: 14px; flex-shrink: 0; }

  .row-label {
    font-size: var(--fs-sm, 14px); color: var(--t2);
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    transition: color .13s;
  }
  .cat-row.off .row-label { color: var(--t3); }

  .cat-pip {
    width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
    transition: opacity .13s;
  }
  .pip-off { opacity: .2; }

  /* ── Edit pencil ────────────────────────────────────────── */
  .edit-btn {
    width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
    font-size: 12px; color: var(--t3);
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity .13s, color .13s, background .13s;
  }
  .cat-row-wrap:hover .edit-btn { opacity: 1; }
  .edit-btn:hover { color: var(--acc); background: rgba(244,184,200,.1); }

  /* ── Empty hint ─────────────────────────────────────────── */
  .empty-hint {
    font-size: var(--fs-xs, 13px); color: var(--t3);
    padding: 6px 8px; font-style: italic;
  }
</style>
