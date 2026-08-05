<script>
  /**
   * ServerPicker.svelte — point this browser at a different backend.
   *
   * Exists so a fork or a self-hoster doesn't have to rebuild the web bundle
   * (or the Android app) just to change where the API lives. The value is
   * saved per-browser in localStorage and takes priority over the build-time
   * and Docker-injected configuration.
   *
   * Lives on the login screen because that is the only moment it is useful:
   * once signed in you are, by definition, already talking to a working
   * server, and switching backends signs you out anyway.
   *
   * The "Test" step is deliberate. Without it the failure mode is a login
   * that reports bad credentials when the real problem is a typo'd host or
   * a CORS policy that doesn't list this origin — which is a genuinely
   * miserable thing to debug from the outside.
   */

  import { slide } from 'svelte/transition';
  import {
    API_BASE_URL, DEFAULT_API_BASE_URL, IS_API_BASE_URL_OVERRIDDEN,
    normaliseApiBaseUrl, setApiBaseUrl, resetApiBaseUrl,
  } from '../lib/config.js';

  let open   = $state(false);
  let value  = $state(API_BASE_URL);
  let status = $state(/** @type {null | 'testing' | 'ok' | 'fail'} */ (null));
  let message = $state('');

  let normalised = $derived(normaliseApiBaseUrl(value));
  let changed    = $derived(normalised !== null && normalised !== API_BASE_URL);

  async function test() {
    if (!normalised) {
      status = 'fail';
      message = 'Enter a valid http:// or https:// address.';
      return;
    }

    status = 'testing';
    message = '';
    try {
      // /auth/config is public and cheap, so it verifies reachability, CORS
      // and that something Self-Calendar-shaped is actually listening —
      // without needing credentials.
      const res = await fetch(`${normalised}/auth/config`, { method: 'GET' });
      if (!res.ok) {
        status = 'fail';
        message = `Server answered with ${res.status}. Is this the API address rather than the web address?`;
        return;
      }
      const body = await res.json();
      if (typeof body?.user_creation !== 'boolean') {
        status = 'fail';
        message = "Something answered, but it doesn't look like a Self Calendar API.";
        return;
      }
      status = 'ok';
      message = 'Connected.';
    } catch {
      // fetch() rejects identically for DNS failure, refused connection and
      // a CORS block, and the browser only reveals which in its console —
      // so name the likely causes rather than pretending to know.
      status = 'fail';
      message = 'Could not reach it. Check the address, that the server is running, '
              + "and that this site's origin is listed in the API's CORS_ORIGINS.";
    }
  }

  function save() {
    try {
      setApiBaseUrl(value); // reloads; nothing after this runs
    } catch (e) {
      status = 'fail';
      message = e?.message ?? 'Could not save that address.';
    }
  }

  function reset() {
    resetApiBaseUrl(); // reloads
  }

  function onKeydown(e) {
    if (e.key === 'Enter') test();
  }
</script>

<div class="server-picker">
  {#if !open}
    <button class="disclosure" onclick={() => { open = true; }}>
      <span class="disclosure-label">Server</span>
      <span class="disclosure-value" title={API_BASE_URL}>
        {API_BASE_URL || 'not configured'}
      </span>
      {#if IS_API_BASE_URL_OVERRIDDEN}
        <span class="badge" title="Set on this device, overriding this build's configuration">custom</span>
      {/if}
    </button>
  {:else}
    <div class="panel" transition:slide={{ duration: 180 }}>
      <label class="field-label" for="server-url">Backend address</label>
      <input
        id="server-url"
        class="field"
        type="url"
        inputmode="url"
        autocomplete="off"
        autocapitalize="off"
        spellcheck="false"
        placeholder="https://calendar.example.com"
        bind:value
        onkeydown={onKeydown}
      />

      <p class="hint">
        The API address, which may differ from the address of this page.
        Saved on this device only.
      </p>

      {#if status && status !== 'testing'}
        <p class="msg" class:ok={status === 'ok'} class:fail={status === 'fail'} role="status">
          {message}
        </p>
      {/if}

      <div class="actions">
        <button class="btn-secondary" onclick={test} disabled={status === 'testing'}>
          {status === 'testing' ? 'Testing…' : 'Test'}
        </button>
        <button class="btn-primary" onclick={save} disabled={!changed}>
          Save &amp; reload
        </button>
      </div>

      <div class="actions">
        {#if IS_API_BASE_URL_OVERRIDDEN}
          <button class="btn-link" onclick={reset}>
            Reset to default ({DEFAULT_API_BASE_URL || 'same origin'})
          </button>
        {/if}
        <button class="btn-link" onclick={() => { open = false; status = null; }}>
          Close
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .server-picker { margin-top: 18px; }

  .disclosure {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 7px 9px;
    border-radius: 8px;
    font-size: .76rem;
    color: var(--t3);
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
    transition: color .15s, border-color .15s, background .15s;
  }
  .disclosure:hover { color: var(--t2); border-color: var(--bdr-soft); }

  .disclosure-label { flex-shrink: 0; font-weight: 600; }

  .disclosure-value {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
    opacity: .85;
  }

  .badge {
    flex-shrink: 0;
    padding: 1px 6px;
    border-radius: 999px;
    font-size: .66rem;
    font-weight: 600;
    color: var(--acc);
    background: var(--acc-bg);
  }

  .panel {
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 12px;
    border: 1px solid var(--bdr-soft);
    border-radius: 10px;
  }

  .field-label {
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--t3);
  }

  .field {
    width: 100%;
    padding: 8px 10px;
    font-size: .84rem;
    color: var(--t1);
    background: var(--bg-app);
    border: 1px solid var(--bdr-soft);
    border-radius: 7px;
    outline: none;
    transition: border-color .15s;
  }
  .field:focus { border-color: var(--acc-dim); }

  .hint {
    margin: 0;
    font-size: .72rem;
    line-height: 1.4;
    color: var(--t3);
  }

  .msg {
    margin: 0;
    font-size: .74rem;
    line-height: 1.4;
  }
  .msg.ok   { color: #4caf7d; }
  .msg.fail { color: #f46464; }

  .actions { display: flex; gap: 6px; }

  .btn-primary, .btn-secondary {
    flex: 1;
    padding: 7px 10px;
    font-size: .8rem;
    font-weight: 500;
    border-radius: 7px;
    cursor: pointer;
    transition: opacity .15s, border-color .15s, color .15s;
  }

  .btn-primary {
    color: var(--on-acc);
    background: var(--acc);
    border: 1px solid transparent;
  }
  .btn-primary:hover:not(:disabled) { opacity: .9; }

  .btn-secondary {
    color: var(--t2);
    background: transparent;
    border: 1px solid var(--bdr-soft);
  }
  .btn-secondary:hover:not(:disabled) { color: var(--t1); border-color: var(--acc-dim); }

  .btn-primary:disabled, .btn-secondary:disabled { opacity: .5; cursor: default; }

  .btn-link {
    flex: 1;
    padding: 4px 2px;
    font-size: .73rem;
    color: var(--t3);
    background: none;
    border: none;
    cursor: pointer;
    transition: color .15s;
  }
  .btn-link:hover { color: var(--acc); }
</style>
