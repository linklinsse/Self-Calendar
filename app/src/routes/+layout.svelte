<script>
  import { onMount } from 'svelte';
  import { App } from '@capacitor/app';
  import { Capacitor } from '@capacitor/core';
  import { cursor, currentView } from '../lib/stores/index.js';
  import { initWidgetSync } from '../lib/widgetSync.js';

  let { children } = $props();

  onMount(() => {
    if (!Capacitor.isNativePlatform()) return;

    initWidgetSync();

    let listenerHandle;
    App.addListener('appUrlOpen', (data) => {
      const match = data.url.match(/date=([\d-]+)/);
      if (match) {
        cursor.set(new Date(match[1]));
        currentView.set('day');
      }
    }).then(h => { listenerHandle = h; });

    return () => { listenerHandle?.remove(); };
  });
</script>

{@render children()}
