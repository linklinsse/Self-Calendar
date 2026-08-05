<script>
  /**
   * CalendarSettings.svelte — Calendar settings modal.
   *
   * Opened when $calSettingsId is set to a calendar id.
   * Tabs:
   *   1. General  — name, colour, description
   *   2. Members  — list of members, invite new, change role, remove
   *
   * Only admins of a calendar can open this modal (Sidebar hides the
   * gear icon for non-admins). The API also enforces this server-side.
   */

  import { fly, fade } from 'svelte/transition';
  import {
    calSettingsId, calendars, currentUser,
    updateCalendar, removeCalendar,
    addCalendarMember, changeCalendarMemberRole, removeCalendarMember,
    showToast,
  } from '../../lib/stores/index.js';
  import { fetchUserCalendars } from '../../lib/services/calendar.service.js';


  // ── Constants ─────────────────────────────────────────────
  /** @type {Array<{value: string, label: string, desc: string}>} */
  const ROLES = [
    { value: 'R',  label: 'Read',       desc: 'Can view events only'           },
    { value: 'W', label: 'Read+Write',  desc: 'Can create and edit events'     },
    { value: 'O', label: 'Admin',       desc: 'Full access + manage members'   },
  ];

  const SWATCH_COLORS = [
    '#f4b8c8', '#b8c9f4', '#b8f4d4', '#f4d8b8',
    '#d8b8f4', '#f4f0b8', '#b8e8f4', '#f4b8e8',
  ];

  // ── Active calendar ────────────────────────────────────────
  let cal = $derived($calSettingsId ? $calendars.find(c => c.id === $calSettingsId) : null);

  // ── Tabs ───────────────────────────────────────────────────
  let activeTab = $state('general');
  $effect(() => { if ($calSettingsId) { activeTab = 'general'; } }); // reset on open

  // ── General tab state ──────────────────────────────────────
  let genName   = $state('');
  let genColor  = $state('');
  let genDesc   = $state('');
  let genSaving = $state(false);

  // FIX: Only re-init when the calendar ID changes (not on every calendar data update).
  let _prevCalId        = $state(null);
  let showDeleteConfirm = $state(false);
  $effect(() => {
    const newId = cal?.id ?? null;
    if (newId !== _prevCalId) {
      _prevCalId = newId;
      if (cal) {
        genName  = cal.title;
        genColor = cal.color;
        genDesc  = cal.description ?? '';
      }
      showDeleteConfirm = false;
    }
  });

  async function saveGeneral() {
    genSaving = true;
    await updateCalendar(cal.id, { title: genName, color: genColor, description: genDesc });
    genSaving = false;
  }

  async function confirmDelete() {
    await removeCalendar(cal.id);
    $calSettingsId = null;
  }

  // ── Members tab state ──────────────────────────────────────
  let members        = $state([]);
  let membersLoading = $state(false);
  let inviteEmail    = $state('');
  let inviteRole     = $state('R');
  let inviting       = $state(false);

  // Sort self to the top
  let sortedMembers = $derived(
    [...members].sort((a, b) => (a.user_id === $currentUser?.id ? -1 : 1) - (b.user_id === $currentUser?.id ? -1 : 1))
  );

  // Load members when the Members tab is activated
  $effect(() => { if (activeTab === 'members' && cal) { loadMembers(); } });

  async function loadMembers() {
    membersLoading = true;
    try {
      members = await fetchUserCalendars(cal.id);
    } catch (e) {
      showToast('Could not load members: ' + e.message, 'error');
    } finally {
      membersLoading = false;
    }
  }

  async function handleInvite() {
    if (!inviteEmail.trim()) return;
    inviting = true;
    try {
      const m = await addCalendarMember(cal.id, inviteEmail.trim(), inviteRole);
      members  = [...members, m];
      inviteEmail = '';
    } catch (e) {
      showToast('Invite failed: ' + e.message, 'error');
    } finally {
      inviting = false;
    }
  }

  // UserCalendar shape: { id, user_id, username, calendar_id, right }
  // m.id   = the link id  (used for PATCH/DELETE)
  // m.right = 'R' | 'W' | 'O'
  async function changeRole(lnkId, right) {
    try {
      await changeCalendarMemberRole(lnkId, right);
      members = members.map(m => m.id === lnkId ? { ...m, right } : m);
    } catch {
      // toast already shown by store
    }
  }

  async function removeMember(lnkId) {
    try {
      await removeCalendarMember(lnkId);
      members = members.filter(m => m.id !== lnkId);
    } catch {
      // toast already shown by store
    }
  }

  // ── Helpers ────────────────────────────────────────────────
  function closeSettings() {
    $calSettingsId    = null;
    showDeleteConfirm = false;
    members           = [];
  }

  function onBackdropClick(e) {
    if (e.target === e.currentTarget) closeSettings();
  }
</script>

{#if cal}

  <!-- Backdrop -->
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="backdrop"
    onclick={onBackdropClick}
    in:fade={{ duration: 200 }}
    out:fade={{ duration: 180 }}
    aria-hidden="true"
  ></div>

  <!-- Modal -->
  <div
    class="modal"
    role="dialog"
    aria-modal="true"
    aria-label="Calendar settings — {cal.title}"
    in:fly={{ y: 28, duration: 320, easing: t => 1 - Math.pow(1-t,3) }}
    out:fly={{ y: 20, duration: 220 }}
  >

    <!-- Header -->
    <div class="modal-hdr" style="border-bottom-color: {cal.color}33">
      <div class="hdr-left">
        <span class="cal-dot" style="background:{cal.color}"></span>
        <h2 class="hdr-title">{cal.title}</h2>
      </div>
      <button class="close-btn" onclick={closeSettings} aria-label="Close settings">✕</button>
    </div>

    <!-- Tabs -->
    <div class="tabs" role="tablist">
      {#each ['general', 'members'] as tab}
        <button
          class="tab"
          class:active={activeTab === tab}
          role="tab"
          aria-selected={activeTab === tab}
          onclick={() => { activeTab = tab; showDeleteConfirm = false; }}
        >
          {#if tab === 'general'}⚙ General
          {:else if tab === 'members'}👥 Members{/if}
        </button>
      {/each}
    </div>

    <!-- ═══════════════════════════════
         GENERAL TAB
    ═══════════════════════════════ -->
    {#if activeTab === 'general'}
      <div class="tab-body">

        <div class="field">
          <label for="cs-name">Calendar name</label>
          <input id="cs-name" type="text" bind:value={genName} placeholder="My calendar" />
        </div>

        <div class="field">
          <label>Colour</label>
          <div class="swatch-row" role="group" aria-label="Calendar colour">
            {#each SWATCH_COLORS as hex}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <div
                class="swatch"
                class:selected={genColor === hex}
                style="background:{hex}"
                role="radio"
                aria-checked={genColor === hex}
                aria-label="Colour {hex}"
                tabindex="0"
                onclick={() => genColor = hex}
                onkeydown={e => e.key === 'Enter' && (genColor = hex)}
              ></div>
            {/each}
          </div>
        </div>

        <div class="field">
          <label for="cs-desc">Description</label>
          <textarea
            id="cs-desc"
            bind:value={genDesc}
            placeholder="Optional description…"
            rows="3"
          ></textarea>
        </div>

        <div class="row-actions">
          <button class="btn-save" onclick={saveGeneral} disabled={genSaving}>
            {genSaving ? 'Saving…' : 'Save changes'}
          </button>
        </div>

        <!-- Danger zone -->
        <div class="danger-zone">
          <h3 class="danger-title">Danger zone</h3>
          {#if !showDeleteConfirm}
            <button class="btn-danger" onclick={() => showDeleteConfirm = true}>
              Delete this calendar
            </button>
          {:else}
            <p class="danger-msg">
              This will permanently delete <strong>{cal.title}</strong> and all its events.
            </p>
            <div class="danger-row">
              <button class="btn-danger-confirm" onclick={confirmDelete}>
                Yes, delete
              </button>
              <button class="btn-cancel" onclick={() => showDeleteConfirm = false}>
                Cancel
              </button>
            </div>
          {/if}
        </div>

      </div>

    <!-- ═══════════════════════════════
         MEMBERS TAB
    ═══════════════════════════════ -->
    {:else if activeTab === 'members'}
      <div class="tab-body">

        <!-- Invite new member -->
        <div class="invite-box">
          <h3 class="invite-title">Invite a person</h3>
          <div class="invite-row">
            <input
              type="text"
              bind:value={inviteEmail}
              placeholder="Username"
              class="invite-email"
              disabled={inviting}
            />
            <select bind:value={inviteRole} class="invite-role" disabled={inviting} required>
              {#each ROLES as r}
                <option value={r.value}>{r.label}</option>
              {/each}
            </select>
            <button class="btn-invite" onclick={handleInvite} disabled={inviting || !inviteEmail.trim()}>
              {inviting ? '…' : 'Invite'}
            </button>
          </div>

          <!-- Role descriptions -->
          <div class="role-legend">
            {#each ROLES as r}
              <div class="role-item">
                <span class="role-pill" class:role-read={r.value === 'R'}
                      class:role-write={r.value === 'W'}
                      class:role-admin={r.value === 'O'}>
                  {r.label}
                </span>
                <span class="role-desc">{r.desc}</span>
              </div>
            {/each}
          </div>
        </div>

        <!-- Member list -->
        {#if membersLoading}
          <p class="loading-msg">Loading members…</p>
        {:else if members.length === 0}
          <p class="empty-msg">No members yet.</p>
        {:else}
          <ul class="member-list">
            {#each sortedMembers as m (m.id)}
              {@const isMe = m.user_id === $currentUser?.id}
              <li class="member-row" class:is-me={isMe}>

                <!-- Info: username + "You" badge -->
                <div class="member-info">
                  <span class="member-name">
                    {m.username}
                    {#if isMe}<span class="you-badge">You</span>{/if}
                  </span>
                </div>

                <!-- Right selector -->
                <select
                  class="role-select"
                  value={m.right}
                  onchange={e => changeRole(m.id, e.target.value)}
                  aria-label="Right for {m.username}"
                >
                  {#each ROLES as r}
                    <option value={r.value}>{r.label}</option>
                  {/each}
                </select>

                <!-- Remove button (hidden for self) -->
                {#if !isMe}
                  <button
                    class="remove-btn"
                    onclick={() => removeMember(m.id)}
                    aria-label="Remove {m.username}"
                    title="Remove member"
                  >✕</button>
                {:else}
                  <div class="remove-placeholder"></div>
                {/if}
              </li>
            {/each}
          </ul>
        {/if}

      </div>

    {/if}

  </div>

{/if}

<style>
  /* ── Backdrop ───────────────────────────────────────────── */
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,.62); backdrop-filter: blur(6px);
    z-index: 69;
  }

  /* ── Modal ──────────────────────────────────────────────── */
  .modal {
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: min(560px, calc(100vw - 24px));
    max-height: min(640px, 90dvh);
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
    border-bottom: 2px solid var(--bdr-soft);
    flex-shrink: 0;
  }
  .hdr-left {
    display: flex; align-items: center; gap: 10px;
  }
  .cal-dot {
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  }
  .hdr-title {
    font-family: var(--f-display);
    font-size: 22px; font-weight: 400; letter-spacing: .02em;
  }
  .close-btn {
    width: 30px; height: 30px; border-radius: var(--r-s);
    color: var(--t3); font-size: 13px;
    display: flex; align-items: center; justify-content: center;
    transition: color .15s, background .15s;
  }
  .close-btn:hover { color: var(--acc); background: var(--acc-bg); }

  /* ── Tabs ───────────────────────────────────────────────── */
  .tabs {
    display: flex; gap: 2px;
    padding: 10px 14px 0;
    border-bottom: 1px solid var(--bdr-soft);
    flex-shrink: 0;
  }
  .tab {
    padding: 7px 14px;
    border-radius: var(--r-s) var(--r-s) 0 0;
    font-size: 12px; font-weight: 500; color: var(--t3);
    transition: color .15s, background .15s;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
  }
  .tab:hover  { color: var(--t2); }
  .tab.active { color: var(--acc); border-bottom-color: var(--acc); }

  /* ── Tab body ───────────────────────────────────────────── */
  .tab-body {
    flex: 1; overflow-y: auto;
    padding: 22px;
    display: flex; flex-direction: column; gap: 18px;
  }

  /* ── Fields ─────────────────────────────────────────────── */
  .field { display: flex; flex-direction: column; gap: 6px; }
  label {
    font-size: 11px; font-weight: 500;
    color: var(--t2); text-transform: uppercase; letter-spacing: .07em;
  }

  /* Colour swatches */
  .swatch-row { display: flex; gap: 9px; flex-wrap: wrap; padding: 2px 0; }
  .swatch {
    width: 26px; height: 26px; border-radius: 50%; cursor: pointer;
    border: 2.5px solid transparent;
    transition: transform .15s, border-color .15s, box-shadow .13s;
  }
  .swatch:hover    { transform: scale(1.15); }
  .swatch.selected {
    border-color: var(--t1);
    box-shadow: 0 0 0 3px rgba(240,234,240,.15);
    transform: scale(1.08);
  }

  /* Danger zone */
  .danger-zone {
    margin-top: 8px; padding-top: 18px;
    border-top: 1px solid rgba(244,100,100,.15);
  }
  .danger-title {
    font-size: 11px; font-weight: 500;
    color: rgba(244,100,100,.6);
    text-transform: uppercase; letter-spacing: .07em; margin-bottom: 10px;
  }
  .danger-msg {
    font-size: 12px; color: var(--t2); margin-bottom: 12px; line-height: 1.5;
  }
  .danger-msg strong { color: var(--t1); }
  .danger-row { display: flex; gap: 10px; }

  .btn-danger {
    padding: 9px 16px; border-radius: var(--r-s);
    border: 1px solid rgba(244,100,100,.3);
    color: #f47070; font-size: 12px;
    transition: all .18s;
  }
  .btn-danger:hover { background: rgba(244,100,100,.08); }

  .btn-danger-confirm {
    padding: 9px 16px; border-radius: var(--r-s);
    background: rgba(244,100,100,.15);
    border: 1px solid rgba(244,100,100,.4);
    color: #f47070; font-size: 12px; font-weight: 600;
    transition: all .18s;
  }
  .btn-danger-confirm:hover { background: rgba(244,100,100,.22); }

  /* ── Invite box ─────────────────────────────────────────── */
  .invite-box {
    background: var(--bg-card); border: 1px solid var(--bdr-soft);
    border-radius: var(--r-m); padding: 16px;
  }
  .invite-title {
    font-size: 12px; font-weight: 500; color: var(--t2);
    margin-bottom: 10px;
  }
  .invite-row {
    display: flex; gap: 8px; flex-wrap: wrap;
  }
  .invite-email { flex: 1; min-width: 160px; }
  .invite-role  { width: 130px; flex-shrink: 0; }
  .btn-invite {
    padding: 10px 16px; border-radius: var(--r-s);
    background: var(--acc); color: #1a0812;
    font-weight: 600; font-size: 12px; flex-shrink: 0;
    transition: opacity .18s;
  }
  .btn-invite:hover:not(:disabled) { opacity: .88; }
  .btn-invite:disabled { opacity: .4; cursor: not-allowed; }

  /* Role legend */
  .role-legend { display: flex; flex-direction: column; gap: 5px; margin-top: 12px; }
  .role-item   { display: flex; align-items: center; gap: 8px; }
  .role-pill   {
    font-size: 9px; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase;
    padding: 2px 8px; border-radius: 20px; flex-shrink: 0;
  }
  .role-read  { background: rgba(160,144,164,.2); color: var(--t2); }
  .role-write { background: rgba(184,201,244,.2); color: #b8c9f4; }
  .role-admin { background: rgba(244,184,200,.2); color: var(--acc); }
  .role-desc  { font-size: 11px; color: var(--t3); }

  /* ── Member list ────────────────────────────────────────── */
  .member-list { list-style: none; display: flex; flex-direction: column; gap: 6px; }

  .member-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 12px;
    background: var(--bg-card); border: 1px solid var(--bdr-soft);
    border-radius: var(--r-m);
    transition: border-color .15s;
  }
  .member-row:hover { border-color: var(--bdr); }
  .member-row.is-me {
    border-color: var(--acc-dim);
    background: var(--acc-bg);
  }

  .member-info {
    flex: 1; display: flex; flex-direction: column; gap: 1px; min-width: 0;
  }
  .member-name {
    font-size: 13px; color: var(--t1);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    display: flex; align-items: center; gap: 7px;
  }
  .you-badge {
    font-size: 10px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase;
    padding: 1px 7px; border-radius: 20px;
    background: var(--acc); color: #1a0812; flex-shrink: 0;
  }
  .remove-placeholder { width: 28px; height: 28px; flex-shrink: 0; }

  .role-select {
    width: auto; padding: 6px 28px 6px 10px; font-size: 12px; flex-shrink: 0;
  }

  .remove-btn {
    width: 28px; height: 28px; border-radius: 6px;
    color: var(--t3); font-size: 12px;
    display: flex; align-items: center; justify-content: center;
    transition: color .15s, background .15s; flex-shrink: 0;
  }
  .remove-btn:hover { color: #f47070; background: rgba(244,100,100,.08); }

  /* ── Shared action buttons ──────────────────────────────────────────────── */
  .row-actions { display: flex; justify-content: flex-end; }

  .btn-save {
    padding: 10px 22px; border-radius: var(--r-s);
    background: linear-gradient(135deg, var(--acc), var(--acc-dim));
    color: #1a0812; font-weight: 600; font-size: 13px;
    box-shadow: 0 2px 12px var(--acc-glow);
    transition: opacity .18s, transform .15s;
  }
  .btn-save:hover:not(:disabled)  { opacity: .9; transform: translateY(-1px); }
  .btn-save:active:not(:disabled) { transform: translateY(0); }
  .btn-save:disabled { opacity: .4; cursor: not-allowed; }

  .btn-cancel {
    padding: 9px 16px; border-radius: var(--r-s);
    border: 1px solid var(--bdr); color: var(--t2); font-size: 12px;
    transition: all .18s;
  }
  .btn-cancel:hover { border-color: var(--acc-dim); color: var(--acc); }

  /* ── Misc ───────────────────────────────────────────────── */
  .loading-msg, .empty-msg {
    font-size: 13px; color: var(--t3); text-align: center;
    padding: 24px 0;
  }
</style>
