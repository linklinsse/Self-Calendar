<script>
  /**
   * LoginScreen.svelte — Sign-in / Sign-up form.
   *
   * Two modes toggled inline:
   *   • Login    — username + password
   *   • Register — username + password + confirm password
   */
  import { fly, fade }                            from 'svelte/transition';
  import { loginUser, registerUser, authLoading } from '../lib/stores/index.js';
  import { fetchAuthConfig }                      from '../lib/services/auth.service.js';
  import ServerPicker                             from './ServerPicker.svelte';
  import { APP_NAME }                             from '../lib/config.js';

  // Split on the first space so everything after it can be italicised
  // without needing {@html} (which would otherwise let a malicious/broken
  // APP_NAME env var inject HTML) — mirrors the previous
  // `.replace(' ', ' <em>') + '</em>'` behavior for a two-word name.
  const appNameSpaceIdx = APP_NAME.indexOf(' ');
  const appNameLead = appNameSpaceIdx === -1 ? APP_NAME : APP_NAME.slice(0, appNameSpaceIdx);
  const appNameRest = appNameSpaceIdx === -1 ? '' : APP_NAME.slice(appNameSpaceIdx + 1);

  /** @type {'login' | 'register'} */
  let mode = $state('login');

  let username = $state('');
  let password = $state('');
  let confirm  = $state('');
  let error    = $state('');

  // Whether this server accepts new accounts (USER_CREATION). Optimistic
  // until the server says otherwise, so a first-run user never sees the tab
  // flicker away while /auth/config is in flight.
  let registrationOpen = $state(true);

  $effect(() => {
    fetchAuthConfig().then(cfg => {
      registrationOpen = cfg.user_creation;
      if (!registrationOpen) mode = 'login';
    });
  });

  // Reset fields whenever mode switches
  $effect(() => {
    mode; username = ''; password = ''; confirm = ''; error = '';
  });

  async function handleSubmit(e) {
    e.preventDefault();
    error = '';

    if (!username.trim()) { error = 'Please enter a username.'; return; }
    if (!password)         { error = 'Please enter a password.';  return; }
    if (mode === 'register') {
      if (password.length < 12) { error = 'Password must be at least 12 characters.'; return; }
      // Mirrors the API's own bound — bcrypt refuses anything over 72 bytes.
      if (new TextEncoder().encode(password).length > 72) {
        error = 'Password must be at most 72 bytes.'; return;
      }
      if (password !== confirm) { error = 'Passwords do not match.'; return; }
    }

    try {
      if (mode === 'login') {
        await loginUser(username.trim(), password);
      } else {
        await registerUser(username.trim(), password);
      }
    } catch (err) {
      error = err.message || (mode === 'login' ? 'Login failed.' : 'Registration failed.');
    }
  }
</script>

<div class="screen" in:fade={{ duration: 260 }}>
  <div class="blob blob-a" aria-hidden="true"></div>
  <div class="blob blob-b" aria-hidden="true"></div>

  <div class="card" in:fly={{ y: 28, duration: 480, easing: t => 1 - Math.pow(1-t,3) }}>

    <!-- Brand -->
    <h1 class="logo">{appNameLead}{#if appNameRest} <em>{appNameRest}</em>{/if}</h1>
    <p class="tagline">Your days, beautifully organised.</p>

    <!-- Mode toggle tabs. Hidden entirely when the server has closed
         registration (USER_CREATION=False) — offering a Create account tab
         that can only ever return an error is worse than not offering it. -->
    {#if registrationOpen}
      <div class="mode-tabs" role="tablist">
        <button
          class="mode-tab"
          class:active={mode === 'login'}
          role="tab"
          aria-selected={mode === 'login'}
          onclick={() => mode = 'login'}
        >Sign in</button>
        <button
          class="mode-tab"
          class:active={mode === 'register'}
          role="tab"
          aria-selected={mode === 'register'}
          onclick={() => mode = 'register'}
        >Create account</button>
      </div>
    {/if}

    {#key mode}
      <form onsubmit={handleSubmit} novalidate in:fly={{ y: 10, duration: 200 }}>

        {#if error}
          <p class="error-banner" role="alert" in:fly={{ y: -6, duration: 160 }}>{error}</p>
        {/if}

        <div class="field">
          <label for="li-user">Username</label>
          <input
            id="li-user" type="text"
            bind:value={username}
            placeholder="your_username"
            autocomplete={mode === 'login' ? 'username' : 'off'}
            required
            disabled={$authLoading}
          />
        </div>

        <div class="field">
          <label for="li-pass">Password</label>
          <input
            id="li-pass" type="password"
            bind:value={password}
            placeholder="••••••••"
            autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
            required
            disabled={$authLoading}
          />
        </div>

        {#if mode === 'register'}
          <div class="field" in:fly={{ y: 8, duration: 180 }}>
            <label for="li-confirm">Confirm password</label>
            <input
              id="li-confirm" type="password"
              bind:value={confirm}
              placeholder="••••••••"
              autocomplete="new-password"
              required
              disabled={$authLoading}
            />
          </div>
        {/if}

        <button class="btn-primary" type="submit" disabled={$authLoading}>
          {#if $authLoading}
            {mode === 'login' ? 'Signing in…' : 'Creating account…'}
          {:else}
            {mode === 'login' ? 'Sign in' : 'Create account'}
          {/if}
        </button>

      </form>
    {/key}

    <!-- Outside the {#key mode} block: switching between Sign in and Create
         account must not collapse an open server panel or discard what has
         been typed into it. -->
    <ServerPicker />

  </div>
</div>

<style>
  .screen {
    position: fixed; inset: 0;
    display: flex; align-items: center; justify-content: center;
    background: var(--bg); overflow: hidden;
  }

  .blob {
    position: absolute; border-radius: 50%;
    filter: blur(90px); pointer-events: none; z-index: 0;
  }
  .blob-a {
    width: 480px; height: 380px;
    background: radial-gradient(circle, var(--acc-glow) 0%, transparent 70%);
    top: -12%; left: -10%;
  }
  .blob-b {
    width: 340px; height: 290px;
    background: radial-gradient(circle, rgba(180,180,244,.07) 0%, transparent 70%);
    bottom: -10%; right: -8%;
  }

  .card {
    position: relative; z-index: 1;
    background: var(--bg-surf); border: 1px solid var(--bdr);
    border-radius: var(--r-xl);
    padding: clamp(28px, 5vw, 48px) clamp(24px, 5vw, 40px);
    width: min(420px, calc(100vw - 32px));
    box-shadow: var(--shadow-card), var(--shadow-glow);
  }

  .logo {
    font-family: var(--f-display);
    font-size: clamp(30px, 7vw, 42px); font-weight: 300;
    color: var(--acc); letter-spacing: .04em; line-height: 1; margin-bottom: 5px;
  }
  .logo :global(em) { font-style: italic; }

  .tagline {
    font-size: 11px; color: var(--t3);
    letter-spacing: .10em; text-transform: uppercase; margin-bottom: 22px;
  }

  /* ── Mode tabs ───────────────────────────────────────────── */
  .mode-tabs {
    display: flex; gap: 2px;
    background: var(--bg-card);
    border: 1px solid var(--bdr-soft);
    border-radius: var(--r-s);
    padding: 3px; margin-bottom: 22px;
  }
  .mode-tab {
    flex: 1; padding: 8px 12px;
    border-radius: calc(var(--r-s) - 2px);
    font-size: var(--fs-xs, 13px); font-weight: 500;
    color: var(--t3); transition: all .16s;
  }
  .mode-tab:hover { color: var(--t2); }
  .mode-tab.active {
    background: var(--acc-bg);
    color: var(--acc);
    border: 1px solid var(--bdr);
    box-shadow: 0 1px 4px rgba(0,0,0,.18);
  }

  /* ── Form ────────────────────────────────────────────────── */
  .error-banner {
    background: rgba(244,100,100,.10); border: 1px solid rgba(244,100,100,.28);
    border-radius: var(--r-s); color: #f49090;
    font-size: var(--fs-xs, 13px); padding: 9px 14px; margin-bottom: 14px;
  }

  .field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }

  label {
    font-size: 11px; font-weight: 500;
    color: var(--t2); text-transform: uppercase; letter-spacing: .07em;
  }

  .btn-primary {
    width: 100%; margin-top: 6px; padding: 13px;
    border-radius: var(--r-s);
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-weight: 600; font-size: var(--fs-sm, 15px);
    letter-spacing: .03em;
    box-shadow: 0 2px 16px var(--acc-glow);
    transition: opacity .18s, transform .15s;
  }
  .btn-primary:hover:not(:disabled)  { opacity: .9; transform: translateY(-1px); }
  .btn-primary:active:not(:disabled) { transform: translateY(0); }
  .btn-primary:disabled              { opacity: .45; cursor: not-allowed; }
</style>
