<script>
  /**
   * CategoryEditor.svelte — Create or edit a category.
   *
   * Opened when $catEditorId is:
   *   -1   → create mode
   *   string → edit mode (existing category id)
   *   null → closed
   *
   * Fields:
   *   • Icon  — emoji input with quick-pick suggestions
   *   • Label — category name
   *   • Color — palette swatches + custom color input
   */

  import { fly, fade } from 'svelte/transition';
  import {
    catEditorId, categories,
    createCategory, updateCategory, removeCategory,
    showToast,
  } from '../../lib/stores/index.js';

  // ── Preset options ─────────────────────────────────────────
  const EMOJI_PRESETS = [
    '🌸','💼','🌿','✨','🌍','🎯','📚','🏃','🎨','🍕',
    '🎵','💊','✈️','🏠','💡','🎁','📅','❤️','⚡','🌙',
  ];

  const COLOR_PALETTE = [
    '#f4b8c8','#b8c9f4','#b8f4d4','#f4d8b8','#d8b8f4',
    '#f4f0b8','#b8e8f4','#f4b8e8','#c4f4b8','#f4c4b8',
    '#b8b8f4','#f4b8b8','#b8f4f4','#e8d4b8','#d4b8e8',
  ];

  // ── Reactive form state ────────────────────────────────────
  $: cat = $catEditorId && $catEditorId !== -1
    ? $categories.find(c => c.id === $catEditorId)
    : null;

  $: isNew = $catEditorId === -1;
  $: isOpen = $catEditorId !== null;

  let form = { icon: '🌸', label: '', color: '#f4b8c8' };
  let labelError = false;
  let saving = false;
  let showDeleteConfirm = false;

  // Re-sync form when editor opens
  $: if (isOpen) {
    if (cat) {
      form = { icon: cat.icon, label: cat.label, color: cat.color };
    } else {
      form = { icon: '🌸', label: '', color: COLOR_PALETTE[0] };
    }
    labelError = false;
    showDeleteConfirm = false;
  }

  // ── Save ───────────────────────────────────────────────────
  async function handleSave() {
    if (!form.label.trim()) { labelError = true; return; }
    saving = true;
    try {
      if (isNew) {
        await createCategory({ ...form, label: form.label.trim() });
      } else {
        await updateCategory(cat.id, { ...form, label: form.label.trim() });
      }
      close();
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    saving = true;
    try {
      await removeCategory(cat.id);
      close();
    } finally {
      saving = false;
    }
  }

  function close() {
    $catEditorId       = null;
    showDeleteConfirm  = false;
  }

  function onBackdropClick(e) {
    if (e.target === e.currentTarget) close();
  }
</script>

{#if isOpen}

  <!-- Backdrop -->
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div
    class="backdrop"
    on:click={onBackdropClick}
    in:fade={{ duration: 200 }}
    out:fade={{ duration: 180 }}
    aria-hidden="true"
  ></div>

  <!-- Modal -->
  <div
    class="modal"
    role="dialog"
    aria-modal="true"
    aria-label="{isNew ? 'New category' : 'Edit category'}"
    in:fly={{ y: 24, duration: 300, easing: t => 1 - Math.pow(1-t,3) }}
    out:fly={{ y: 20, duration: 200 }}
  >

    <!-- Header with live preview -->
    <div class="modal-hdr">
      <div class="preview-badge" style="background:{form.color}22; border-color:{form.color}44">
        <span class="preview-icon">{form.icon}</span>
        <span class="preview-label" style="color:{form.color}">
          {form.label || (isNew ? 'New category' : cat?.label)}
        </span>
      </div>
      <button class="close-btn" on:click={close} aria-label="Close">✕</button>
    </div>

    <div class="modal-body">

      <!-- ── Icon ───────────────────────────────────────────── -->
      <div class="field">
        <label for="cat-icon">Icon</label>
        <input
          id="cat-icon"
          type="text"
          bind:value={form.icon}
          placeholder="🌸"
          class="icon-input"
          maxlength="4"
        />
        <!-- Quick-pick emoji grid -->
        <div class="emoji-grid" role="group" aria-label="Emoji presets">
          {#each EMOJI_PRESETS as emoji}
            <button
              class="emoji-btn"
              class:active={form.icon === emoji}
              on:click={() => form.icon = emoji}
              aria-label={emoji}
              type="button"
            >{emoji}</button>
          {/each}
        </div>
      </div>

      <!-- ── Label ──────────────────────────────────────────── -->
      <div class="field" class:has-error={labelError}>
        <label for="cat-label">Name</label>
        <input
          id="cat-label"
          type="text"
          bind:value={form.label}
          on:input={() => labelError = false}
          placeholder="e.g. Health, Work, Travel…"
          autocomplete="off"
        />
        {#if labelError}
          <span class="err-msg" role="alert">Please enter a name.</span>
        {/if}
      </div>

      <!-- ── Color ──────────────────────────────────────────── -->
      <div class="field">
        <label>Colour</label>
        <div class="swatches" role="group" aria-label="Category colour">
          {#each COLOR_PALETTE as hex (hex)}
            <!-- svelte-ignore a11y-click-events-have-key-events -->
            <div
              class="swatch"
              class:selected={form.color === hex}
              style="background:{hex}"
              role="radio"
              aria-checked={form.color === hex}
              tabindex="0"
              on:click={() => form.color = hex}
              on:keydown={e => e.key === 'Enter' && (form.color = hex)}
            ></div>
          {/each}

          <!-- Custom input -->
          <label class="custom-swatch" title="Custom colour">
            <input
              type="color"
              value={form.color}
              on:input={e => form.color = e.target.value}
            />
            <span aria-hidden="true">🎨</span>
          </label>
        </div>

        <div class="color-preview">
          <span class="preview-dot" style="background:{form.color}"></span>
          <span class="preview-hex">{form.color}</span>
        </div>
      </div>

      <!-- ── Danger zone (edit mode only) ──────────────────── -->
      {#if !isNew}
        <div class="danger-zone">
          {#if !showDeleteConfirm}
            <button class="btn-danger" on:click={() => showDeleteConfirm = true}>
              Delete category
            </button>
          {:else}
            <p class="danger-msg">Delete <strong>{cat?.label}</strong>? This cannot be undone.</p>
            <div class="danger-row">
              <button
                class="btn-danger-confirm"
                on:click={handleDelete}
                disabled={saving}
              >
                {saving ? '…' : 'Yes, delete'}
              </button>
              <button class="btn-cancel-sm" on:click={() => showDeleteConfirm = false}>
                Cancel
              </button>
            </div>
          {/if}
        </div>
      {/if}

    </div>

    <!-- Footer -->
    <div class="modal-ftr">
      <button class="btn-cancel" on:click={close} disabled={saving}>Cancel</button>
      <button class="btn-save"   on:click={handleSave} disabled={saving}>
        {saving ? 'Saving…' : isNew ? 'Create category' : 'Save changes'}
      </button>
    </div>

  </div>

{/if}

<style>
  /* ── Backdrop ───────────────────────────────────────────── */
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.60); backdrop-filter: blur(5px);
    z-index: 69;
  }

  /* ── Modal ──────────────────────────────────────────────── */
  .modal {
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: min(460px, calc(100vw - 24px));
    max-height: min(90dvh, 640px);
    background: var(--bg-surf);
    border: 1px solid var(--bdr);
    border-radius: var(--r-xl);
    z-index: 70;
    display: flex; flex-direction: column;
    box-shadow: var(--shadow-card), var(--shadow-glow);
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .modal {
      top: auto; left: 0; right: 0; bottom: 0;
      transform: none;
      width: 100%;
      border-radius: var(--r-xl) var(--r-xl) 0 0;
      max-height: 92dvh;
    }
  }

  /* ── Header ─────────────────────────────────────────────── */
  .modal-hdr {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 22px 14px;
    border-bottom: 1px solid var(--bdr-soft);
    flex-shrink: 0;
  }

  /* Live preview badge */
  .preview-badge {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 14px; border-radius: 20px;
    border: 1px solid transparent;
    transition: background .2s, border-color .2s;
  }
  .preview-icon  { font-size: 18px; line-height: 1; }
  .preview-label {
    font-size: 14px; font-weight: 500;
    transition: color .2s;
    max-width: 180px; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
  }

  .close-btn {
    width: 30px; height: 30px; border-radius: var(--r-s);
    color: var(--t3); font-size: 13px;
    display: flex; align-items: center; justify-content: center;
    transition: color .15s, background .15s;
  }
  .close-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Body ───────────────────────────────────────────────── */
  .modal-body {
    flex: 1; overflow-y: auto;
    padding: 20px;
    display: flex; flex-direction: column; gap: 18px;
  }

  /* ── Fields ─────────────────────────────────────────────── */
  .field { display: flex; flex-direction: column; gap: 7px; }
  .field.has-error input { border-color: #f47070; }

  label {
    font-size: 11px; font-weight: 500;
    color: var(--t2); text-transform: uppercase; letter-spacing: .07em;
  }
  .err-msg { font-size: 11px; color: #f47070; }

  .icon-input {
    font-size: 20px; text-align: center;
    width: 60px; padding: 8px;
  }

  /* ── Emoji quick-pick ───────────────────────────────────── */
  .emoji-grid {
    display: flex; flex-wrap: wrap; gap: 6px;
    padding: 2px 0;
  }
  .emoji-btn {
    width: 34px; height: 34px; border-radius: var(--r-s);
    font-size: 18px; line-height: 1;
    display: flex; align-items: center; justify-content: center;
    transition: background .13s, transform .13s;
    border: 1.5px solid transparent;
  }
  .emoji-btn:hover { background: var(--acc-bg); transform: scale(1.1); }
  .emoji-btn.active {
    background: var(--acc-bg); border-color: var(--acc-dim);
    transform: scale(1.05);
  }

  /* ── Color swatches ─────────────────────────────────────── */
  .swatches { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

  .swatch {
    width: 26px; height: 26px; border-radius: 50%;
    cursor: pointer; border: 2.5px solid transparent;
    transition: transform .14s, border-color .14s, box-shadow .14s;
  }
  .swatch:hover    { transform: scale(1.15); }
  .swatch.selected {
    border-color: var(--t1);
    box-shadow: 0 0 0 3px rgba(240,234,240,.15);
    transform: scale(1.08);
  }

  .custom-swatch {
    width: 26px; height: 26px; border-radius: 50%;
    cursor: pointer; overflow: hidden;
    border: 1.5px dashed var(--bdr);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; transition: border-color .14s;
  }
  .custom-swatch:hover { border-color: var(--acc-dim); }
  .custom-swatch input[type="color"] {
    position: absolute; opacity: 0; width: 0; height: 0;
  }

  .color-preview {
    display: flex; align-items: center; gap: 8px; margin-top: 2px;
  }
  .preview-dot {
    width: 12px; height: 12px; border-radius: 50;
    border-radius: 50%; flex-shrink: 0; transition: background .2s;
  }
  .preview-hex {
    font-family: var(--f-mono);
    font-size: 11px; color: var(--t3); letter-spacing: .04em;
  }

  /* ── Danger zone ────────────────────────────────────────── */
  .danger-zone {
    padding-top: 14px; border-top: 1px solid rgba(244,100,100,.15);
  }
  .danger-msg {
    font-size: 12px; color: var(--t2); margin-bottom: 10px; line-height: 1.5;
  }
  .danger-msg strong { color: var(--t1); }
  .danger-row { display: flex; gap: 10px; }

  .btn-danger {
    font-size: 12px; color: #f47070;
    border: 1px solid rgba(244,100,100,.25);
    padding: 8px 14px; border-radius: var(--r-s);
    transition: all .16s;
  }
  .btn-danger:hover { background: rgba(244,100,100,.08); }

  .btn-danger-confirm {
    padding: 8px 14px; border-radius: var(--r-s);
    background: rgba(244,100,100,.15);
    border: 1px solid rgba(244,100,100,.35);
    color: #f47070; font-size: 12px; font-weight: 600;
    transition: all .16s;
  }
  .btn-danger-confirm:hover { background: rgba(244,100,100,.22); }
  .btn-danger-confirm:disabled { opacity: .5; cursor: not-allowed; }

  .btn-cancel-sm {
    padding: 8px 14px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2); font-size: 12px;
    transition: all .16s;
  }
  .btn-cancel-sm:hover { border-color: var(--acc-dim); color: var(--acc); }

  /* ── Footer ─────────────────────────────────────────────── */
  .modal-ftr {
    padding: 14px 20px; border-top: 1px solid var(--bdr-soft);
    display: flex; gap: 10px; flex-shrink: 0;
  }
  .btn-cancel {
    flex: 1; padding: 11px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2); font-size: 13px;
    transition: all .18s;
  }
  .btn-cancel:hover:not(:disabled) { border-color: var(--acc-dim); color: var(--acc); }
  .btn-cancel:disabled { opacity: .45; cursor: not-allowed; }

  .btn-save {
    flex: 2; padding: 11px; border-radius: var(--r-s);
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-weight: 600; font-size: 13px;
    box-shadow: 0 2px 12px var(--acc-glow);
    transition: opacity .18s, transform .15s;
  }
  .btn-save:hover:not(:disabled)  { opacity: .9; transform: translateY(-1px); }
  .btn-save:active:not(:disabled) { transform: translateY(0); }
  .btn-save:disabled { opacity: .45; cursor: not-allowed; }
</style>
