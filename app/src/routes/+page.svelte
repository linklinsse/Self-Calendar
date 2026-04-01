<script>
  /**
   * App.svelte — Root component.
   * Applies the active theme on mount, handles global Escape key,
   * routes between LoginScreen and AppShell.
   */
  import { onMount }        from 'svelte';
  import { activeThemeId, applyTheme, resolveTheme } from '../lib/themes/index.js';
  import { currentView }    from '../lib/stores/ui.js';
  import { DEFAULT_VIEW }   from '../lib/config.js';
  import {
    isLoggedIn, panelEvent, modalEventId,
    filterDrawerOpen, sidebarOpen, calSettingsId,
    catEditorId, calCreatorOpen, closePanel,
  } from '../lib/stores/index.js';

  import LoginScreen from '../components/LoginScreen.svelte';
  import AppShell    from '../components/AppShell.svelte';
  import Toast       from '../components/ui/Toast.svelte';

  // Apply the persisted theme on first render
  onMount(() => {
    // applyTheme(resolveTheme($activeThemeId));
    currentView.set(DEFAULT_VIEW);
  });

  // Re-apply whenever the theme id changes (ThemePicker)
  $: if (typeof document !== 'undefined') {
    applyTheme(resolveTheme($activeThemeId));
  }

  // Global Escape: close the topmost open overlay
  function onKeydown(e) {
    if (e.key !== 'Escape') return;
    if ($panelEvent)        { closePanel();                  return; }
    if ($modalEventId)      { modalEventId.set(null);        return; }
    if ($catEditorId)       { catEditorId.set(null);         return; }
    if ($calCreatorOpen)    { calCreatorOpen.set(false);     return; }
    if ($calSettingsId)     { calSettingsId.set(null);       return; }
    if ($filterDrawerOpen)  { filterDrawerOpen.set(false);   return; }
    if ($sidebarOpen)       { sidebarOpen.set(false);        return; }
  }
</script>

<svelte:window on:keydown={onKeydown} />

<svelte:head>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      height: 100%; overflow: hidden;
      font-family: var(--f-body, system-ui, sans-serif);
      background: var(--bg, #0d0d12);
      color: var(--t1, #f0eaf2);
      font-size: var(--fs-md, 16px);
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    #app { height: 100%; display: flex; flex-direction: column; }

    button {
      cursor: pointer; border: none; background: none;
      font-family: inherit; color: inherit; font-size: inherit;
    }
    button:focus-visible {
      outline: 2px solid var(--acc); outline-offset: 2px; border-radius: 4px;
    }
    input, select, textarea {
      font-family: inherit; font-size: var(--fs-sm, 15px);
      background: var(--bg-raised); border: 1px solid var(--bdr);
      color: var(--t1); border-radius: var(--r-s);
      padding: 10px 14px; outline: none; width: 100%;
      transition: border-color .18s, box-shadow .18s;
      -webkit-appearance: none; appearance: none;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--acc-dim);
      box-shadow: 0 0 0 3px rgba(244,184,200,.07);
    }
    input::placeholder, textarea::placeholder { color: var(--t3); }
    select {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23a090a4'/%3E%3C/svg%3E");
      background-repeat: no-repeat; background-position: right 12px center;
      padding-right: 34px;
    }
    select option { background: var(--bg-card); }
    textarea { resize: vertical; min-height: 72px; line-height: 1.55; }
    ::-webkit-scrollbar        { width: 3px; height: 3px; }
    ::-webkit-scrollbar-track  { background: transparent; }
    ::-webkit-scrollbar-thumb  { background: var(--bdr); border-radius: 3px; }
  </style>
</svelte:head>

{#if $isLoggedIn}
  <AppShell />
{:else}
  <LoginScreen />
{/if}

<Toast />
