<script>
  /**
   * PasswordChanger.svelte — change the signed-in user's password.
   *
   * Collapsed to a single button until used, since it lives in the sidebar
   * footer next to Sign out and is a rare action.
   *
   * Note the API invalidates every existing token on success (token_version
   * is bumped), so `changePassword` in the store re-authenticates
   * immediately. The user stays signed in; that is intentional, but it does
   * mean a failure *after* the password has changed leaves them needing to
   * sign in again — which the error message says explicitly rather than
   * leaving them guessing.
   */

  import { slide } from 'svelte/transition';
  import { changePassword, showToast } from '../../lib/stores/index.js';

  let open       = $state(false);
  let oldPassword = $state('');
  let newPassword = $state('');
  let confirm     = $state('');
  let error       = $state('');
  let busy        = $state(false);

  function reset() {
    oldPassword = ''; newPassword = ''; confirm = ''; error = '';
  }

  function close() { open = false; reset(); }

  async function submit() {
    error = '';

    if (!oldPassword) { error = 'Enter your current password.'; return; }
    if (newPassword.length < 12) {
      error = 'New password must be at least 12 characters.'; return;
    }
    // Mirrors the API's own bound — bcrypt refuses anything over 72 bytes,
    // and the server rejects it, so catch it before the round trip.
    if (new TextEncoder().encode(newPassword).length > 72) {
      error = 'New password must be at most 72 bytes.'; return;
    }
    if (newPassword !== confirm) { error = 'New passwords do not match.'; return; }
    if (newPassword === oldPassword) {
      error = 'New password must be different from the current one.'; return;
    }

    busy = true;
    try {
      await changePassword(oldPassword, newPassword);
      showToast('Password changed.', 'success');
      close();
    } catch (e) {
      // The API returns 401 INVALID_CREDENTIALS when the old password is
      // wrong — by far the most common failure, so name it rather than
      // showing a generic message.
      error = e?.code === 'INVALID_CREDENTIALS'
        ? 'Your current password is incorrect.'
        : (e?.message || 'Could not change your password.');
    } finally {
      busy = false;
    }
  }

  function onKeydown(e) {
    if (e.key === 'Enter' && !busy) submit();
  }
</script>

{#if !open}
  <button class="foot-btn" onclick={() => { open = true; }}>
    <span aria-hidden="true">🔑</span> Change password
  </button>
{:else}
  <div class="pw-form" transition:slide={{ duration: 180 }}>
    <p class="pw-label">Change password</p>

    <input
      class="pw-input"
      type="password"
      placeholder="Current password"
      autocomplete="current-password"
      bind:value={oldPassword}
      onkeydown={onKeydown}
      disabled={busy}
    />
    <input
      class="pw-input"
      type="password"
      placeholder="New password"
      autocomplete="new-password"
      bind:value={newPassword}
      onkeydown={onKeydown}
      disabled={busy}
    />
    <input
      class="pw-input"
      type="password"
      placeholder="Confirm new password"
      autocomplete="new-password"
      bind:value={confirm}
      onkeydown={onKeydown}
      disabled={busy}
    />

    {#if error}
      <p class="pw-error" role="alert">{error}</p>
    {/if}

    <div class="pw-actions">
      <button class="pw-save" onclick={submit} disabled={busy}>
        {busy ? 'Saving…' : 'Save'}
      </button>
      <button class="pw-cancel" onclick={close} disabled={busy}>Cancel</button>
    </div>
  </div>
{/if}

<style>
  /* Mirrors Sidebar's own .foot-btn — Svelte scopes styles per component, so
     the sidebar's rule doesn't reach this button. Keep the two in step. */
  .foot-btn {
    display: flex; align-items: center; gap: 10px;
    width: 100%; padding: 9px 8px; border-radius: var(--r-s);
    font-size: var(--fs-sm, 15px); color: var(--t3);
    transition: color .18s, background .18s;
    white-space: nowrap;
  }
  .foot-btn:hover { color: var(--acc); background: var(--acc-bg); }

  .pw-form {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 8px 0 4px;
  }

  .pw-label {
    margin: 0 0 2px;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--t2);
  }

  .pw-input {
    width: 100%;
    padding: 7px 9px;
    font-size: .82rem;
    color: var(--t1);
    background: var(--bg-app);
    border: 1px solid var(--bdr-soft);
    border-radius: 7px;
    outline: none;
    transition: border-color .15s;
  }
  .pw-input:focus     { border-color: var(--acc-dim); }
  .pw-input:disabled  { opacity: .6; }

  .pw-error {
    margin: 2px 0 0;
    font-size: .74rem;
    line-height: 1.35;
    color: #f46464;
  }

  .pw-actions {
    display: flex;
    gap: 6px;
    margin-top: 4px;
  }

  .pw-save, .pw-cancel {
    flex: 1;
    padding: 7px 10px;
    font-size: .8rem;
    font-weight: 500;
    border-radius: 7px;
    cursor: pointer;
    transition: opacity .15s, border-color .15s, color .15s;
  }

  .pw-save {
    color: var(--on-acc);
    background: var(--acc);
    border: 1px solid transparent;
  }
  .pw-save:hover:not(:disabled) { opacity: .9; }

  .pw-cancel {
    color: var(--t2);
    background: transparent;
    border: 1px solid var(--bdr-soft);
  }
  .pw-cancel:hover:not(:disabled) { color: var(--t1); border-color: var(--acc-dim); }

  .pw-save:disabled, .pw-cancel:disabled { opacity: .6; cursor: default; }
</style>
