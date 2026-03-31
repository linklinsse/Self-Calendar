<script>
  /**
   * CategoryList.svelte — Left-sidebar section: category filter list.
   *
   * Features:
   *  • Toggle category visibility (filter) via pill rows
   *  • Pencil icon → CategoryEditor modal (edit)
   *  • "＋" button → CategoryEditor modal (create)
   */

  import {
    categories, catEditorId,
    toggleCategory,
  } from '../../lib/stores/index.js';
</script>

<section class="cat-list">

  <!-- Section header -->
  <div class="sec-hdr">
    <h3 class="sec-title">Categories</h3>
    <button
      class="hdr-btn"
      on:click={() => $catEditorId = -1}
      aria-label="Create new category"
      title="New category"
    >＋</button>
  </div>

  <!-- Category rows -->
  {#each $categories as cat (cat.id)}
    <div class="cat-row-wrap">
      <button
        class="cat-row"
        class:off={!cat.on}
        on:click={() => toggleCategory(cat.id)}
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
        on:click={() => $catEditorId = cat.id}
        aria-label="Edit {cat.label}"
        title="Edit category"
      >✎</button>
    </div>
  {/each}

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

  /* ── Category row wrapper ───────────────────────────────── */
  .cat-row-wrap {
    display: flex; align-items: center;
    border-radius: 20px;
    transition: background .13s;
  }
  .cat-row-wrap:hover { background: var(--acc-bg); }

  /* ── Category row button ────────────────────────────────── */
  .cat-row {
    display: flex; align-items: center; gap: 10px;
    flex: 1; padding: 7px 8px; border-radius: 20px;
    text-align: left; min-width: 0;
    transition: background .13s;
  }
  .cat-row-wrap .cat-row:hover { background: none; }

  .cat-icon { font-size: 15px; flex-shrink: 0; }

  .row-label {
    font-size: var(--fs-sm, 15px); color: var(--t2);
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
</style>
