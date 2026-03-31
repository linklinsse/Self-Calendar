<script>
  /**
   * ThemePicker.svelte — Theme selector.
   *
   * Always rendered inline — no floating popup.
   * Shows a collapsible section with theme preview cards.
   * Selecting a theme applies it immediately and persists to localStorage.
   */

  import { slide } from 'svelte/transition';
  import { THEME_LIST, activeThemeId, applyTheme, resolveTheme }
    from '../../lib/themes/index.js';

  let open = false;

  function pickTheme(id) {
    activeThemeId.set(id);
    applyTheme(resolveTheme(id));
    open = false;
  }

  $: currentTheme = THEME_LIST.find(t => t.id === $activeThemeId) ?? THEME_LIST[0];
</script>

<div class="theme-picker">

  <!-- Toggle row — shows current theme name -->
  <button
    class="toggle-btn"
    on:click={() => open = !open}
    aria-expanded={open}
    aria-label="Change theme"
  >
    <!-- Mini swatch of current theme -->
    <div class="mini-swatch" style="background:{currentTheme.bgBase}">
      <div class="mini-acc" style="background:{currentTheme.accent}"></div>
    </div>
    <span class="current-name">{currentTheme.name}</span>
    <span class="chevron" class:open aria-hidden="true">▾</span>
  </button>

  <!-- Collapsible grid -->
  {#if open}
    <div class="grid-wrap" transition:slide={{ duration: 220 }}>
      <div class="picker-grid" role="group" aria-label="Choose theme">
        {#each THEME_LIST as theme}
          <button
            class="theme-card"
            class:active={$activeThemeId === theme.id}
            on:click={() => pickTheme(theme.id)}
            aria-pressed={$activeThemeId === theme.id}
            aria-label="Apply {theme.name} theme"
            title={theme.name}
          >
            <!-- Preview swatch -->
            <div class="preview" style="background:{theme.bgBase}; border-color:{theme.border}">
              <div class="preview-surf" style="background:{theme.bgSurface}">
                <div class="preview-acc"  style="background:{theme.accent}"></div>
                <div class="preview-acc2" style="background:{theme.accentDim}; opacity:.6"></div>
              </div>
            </div>
            <span class="theme-name">{theme.name}</span>
            {#if $activeThemeId === theme.id}
              <span class="active-dot" aria-hidden="true"
                style="background:{theme.accent}"></span>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  {/if}

</div>

<style>
  /* ── Wrapper ─────────────────────────────────────────────── */
  .theme-picker {
    width: 100%;
    border: 1px solid var(--bdr-soft);
    border-radius: var(--r-s);
    overflow: hidden;
    background: var(--bg-card);
  }

  /* ── Toggle button ──────────────────────────────────────── */
  .toggle-btn {
    width: 100%; padding: 8px 10px;
    display: flex; align-items: center; gap: 9px;
    text-align: left; cursor: pointer;
    transition: background .13s;
  }
  .toggle-btn:hover { background: var(--acc-bg); }

  /* Tiny 2-colour swatch of the current theme */
  .mini-swatch {
    width: 24px; height: 16px; border-radius: 4px;
    overflow: hidden; flex-shrink: 0;
    border: 1px solid rgba(255,255,255,.12);
    display: flex; align-items: flex-end;
  }
  .mini-acc {
    width: 10px; height: 8px; border-radius: 1px; margin: 2px;
  }

  .current-name {
    flex: 1; font-size: var(--fs-xs, 13px); color: var(--t2);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  .chevron {
    font-size: 11px; color: var(--t3); flex-shrink: 0;
    transition: transform .18s;
  }
  .chevron.open { transform: rotate(180deg); }

  /* ── Grid wrapper ───────────────────────────────────────── */
  .grid-wrap {
    border-top: 1px solid var(--bdr-soft);
    padding: 10px;
    background: var(--bg-surf);
  }

  .picker-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
    gap: 7px;
  }

  /* ── Theme card ─────────────────────────────────────────── */
  .theme-card {
    display: flex; flex-direction: column; align-items: center; gap: 5px;
    padding: 7px 5px;
    border-radius: var(--r-s);
    border: 2px solid transparent;
    background: var(--bg-card);
    cursor: pointer; position: relative;
    transition: border-color .14s, background .14s;
  }
  .theme-card:hover  { background: var(--bg-raised); border-color: var(--bdr); }
  .theme-card.active { border-color: var(--acc); }

  /* Preview swatch */
  .preview {
    width: 52px; height: 32px; border-radius: 5px;
    overflow: hidden; display: flex; align-items: flex-end;
    border: 1px solid rgba(0,0,0,.15);
    flex-shrink: 0;
  }
  .preview-surf {
    width: 58%; height: 100%;
    display: flex; flex-direction: column; justify-content: flex-end;
    padding: 3px; gap: 2px;
  }
  .preview-acc  { height: 5px; border-radius: 2px; }
  .preview-acc2 { height: 3px; border-radius: 2px; }

  .theme-name {
    font-size: 10px; color: var(--t2); text-align: center;
    line-height: 1.2; max-width: 100%;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* Active dot — uses the theme's own accent colour so it's always visible */
  .active-dot {
    position: absolute; top: 4px; right: 4px;
    width: 6px; height: 6px; border-radius: 50%;
  }
</style>
