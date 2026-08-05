<script>
  /**
   * Toast.svelte — Global notification toast.
   * Supports type: 'info' | 'success' | 'error' for colour coding.
   */

  import { fly } from 'svelte/transition';
  import { toast } from '../../lib/stores/index.js';
</script>

{#if $toast}
  <div
    class="toast"
    class:success={$toast.type === 'success'}
    class:error={$toast.type === 'error'}
    role="status"
    aria-live="polite"
    in:fly={{ y: 16, duration: 260, easing: t => 1 - Math.pow(1-t,3) }}
    out:fly={{ y: 16, duration: 200 }}
  >
    <span class="dot" aria-hidden="true">
      {#if $toast.type === 'success'}✓
      {:else if $toast.type === 'error'}✕
      {:else}·{/if}
    </span>
    {$toast.text}
  </div>
{/if}

<style>
  .toast {
    position: fixed;
    bottom: 80px; left: 50%;
    transform: translateX(-50%);
    background: var(--bg-card);
    border: 1px solid var(--bdr);
    border-radius: 24px;
    padding: 10px 18px;
    font-size: var(--fs-xs, 13px); color: var(--t2);
    box-shadow: var(--shadow-card);
    z-index: 300;
    white-space: nowrap;
    pointer-events: none;
    display: flex; align-items: center; gap: 8px;
    max-width: calc(100vw - 32px);
    text-overflow: ellipsis; overflow: hidden;
  }
  .toast.success { border-color: rgba(184,244,212,.3); }
  .toast.error   { border-color: rgba(244,100,100,.3); }

  .dot { font-size: var(--fs-sm, 15px); flex-shrink: 0; }
  .toast.success .dot { color: #b8f4d4; }
  .toast.error   .dot { color: #f49090; }
  .toast:not(.success):not(.error) .dot { color: var(--acc); }

  @media (min-width: 769px) { .toast { bottom: 28px; } }
</style>
