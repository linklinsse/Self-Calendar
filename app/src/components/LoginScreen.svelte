<script>
  /**
   * LoginScreen.svelte
   *
   * Two modes toggled by the user:
   *   sign-in  — username + password → loginUser()
   *   register — username + password + confirm → registerUser()
   *
   * No "guest" option.
   */
  import { fly, fade }               from 'svelte/transition';
  import { loginUser, registerUser, authLoading } from '../lib/stores/index.js';
  import { APP_NAME }                from '../lib/config.js';

  /** 'login' | 'register' */
  let mode     = $state('login');
  let username = $state('');
  let password = $state('');
  let confirm  = $state('');
  let error    = $state('');

  function switchMode(m) {
    mode = m; error = ''; username = ''; password = ''; confirm = '';
  }

  async function handleSubmit(e) {
    e.preventDefault();
    error = '';

    if (!username.trim()) { error = 'Please enter a username.'; return; }
    if (!password)         { error = 'Please enter a password.';  return; }

    if (mode === 'register') {
      if (password.length < 6) { error = 'Password must be at least 6 characters.'; return; }
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
    <h1 class="logo">{@html APP_NAME.replace(' ', ' <em>') + '</em>'}</h1>
    <p class="tagline">Your days, beautifully organised.</p>

    <!-- Mode tabs -->
    <div class="tabs" role="tablist">
      <button
        class="tab" class:active={mode === 'login'}
        role="tab" aria-selected={mode === 'login'}
        onclick={() => switchMode('login')}
      >Sign in</button>
      <button
        class="tab" class:active={mode === 'register'}
        role="tab" aria-selected={mode === 'register'}
        onclick={() => switchMode('register')}
      >Create account</button>
    </div>

    <!-- Form -->
    <form onsubmit={handleSubmit} novalidate>

      {#if error}
        <p class="error-banner" role="alert" in:fly={{ y: -6, duration: 160 }}>{error}</p>
      {/if}

      <!-- Username -->
      <div class="field">
        <label for="li-user">Username</label>
        <input
          id="li-user" type="text"
          bind:value={username}
          placeholder="your_username"
          autocomplete={mode === 'login' ? 'username' : 'username'}
          required
          disabled={$authLoading}
        />
      </div>

      <!-- Password -->
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

      <!-- Confirm password (register only) -->
      {#if mode === 'register'}
        <div class="field" in:fly={{ y: -8, duration: 200 }}>
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
    letter-spacing: .10em; text-transform: uppercase; margin-bottom: 24px;
  }

  /* Tabs */
  .tabs {
    display: flex; gap: 0;
    background: var(--bg-raised); border-radius: var(--r-s);
    padding: 3px; margin-bottom: 22px;
  }
  .tab {
    flex: 1; padding: 8px 12px; border-radius: 6px;
    font-size: var(--fs-xs, 13px); font-weight: 500; color: var(--t3);
    transition: all .15s;
  }
  .tab.active { background: var(--bg-surf); color: var(--t1); }

  /* Form */
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
