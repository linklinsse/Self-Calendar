<script>
  import { onMount } from 'svelte';
  import { App } from '@capacitor/app';
  import { Capacitor } from '@capacitor/core';
  import {
    cursor, currentView, modalEventId, modalOccurrenceDate, showToast,
  } from '../lib/stores/index.js';
  import { fetchEvent } from '../lib/services/event.service.js';
  import { initWidgetSync } from '../lib/widgetSync.js';

  let { children } = $props();

  /**
   * selfcalendar://event?id=… — written into events exported to the device
   * calendar (see systemCalendar.service.js), so the copy sitting in the
   * user's own calendar app can bring them back here.
   *
   * The event is fetched by id rather than looked up in the `events` store:
   * that store only holds the currently-loaded date range, and an event
   * linked from an external calendar is very often outside it. Fetching
   * first also gives us its date, so the cursor can be moved there — which
   * is what triggers CalendarBody's own load and populates the store, so
   * the modal has something to render by the time it opens.
   */
  async function openEventById(id) {
    try {
      const ev = await fetchEvent(id);
      cursor.set(new Date(ev.startDate));
      currentView.set('day');
      modalOccurrenceDate.set(null);
      modalEventId.set(ev.id);
    } catch {
      // Deleted since the export, or belonging to an account that is not the
      // one currently signed in. Landing on the app with nothing happening
      // and no explanation is worse than saying so.
      showToast('That event could no longer be found.', 'error');
    }
  }

  /** selfcalendar://day?date=YYYY-MM-DD — used by the home-screen widget. */
  function openDay(dateStr) {
    cursor.set(new Date(dateStr));
    currentView.set('day');
  }

  function handleUrl(rawUrl) {
    let url;
    try {
      url = new URL(rawUrl);
    } catch {
      return; // not a URL we can parse; nothing sensible to do
    }

    // `host` is what the manifest's intent-filter matches on
    // (selfcalendar://event / selfcalendar://day).
    if (url.host === 'event') {
      const id = url.searchParams.get('id');
      if (id) openEventById(id);
      return;
    }

    if (url.host === 'day') {
      const date = url.searchParams.get('date');
      if (date) openDay(date);
    }
  }

  onMount(() => {
    if (!Capacitor.isNativePlatform()) return;

    initWidgetSync();

    let listenerHandle;
    App.addListener('appUrlOpen', (data) => handleUrl(data.url))
      .then(h => { listenerHandle = h; });

    // A link tapped while the app is closed launches it rather than firing
    // appUrlOpen, so the launch URL has to be read once on mount too.
    App.getLaunchUrl()
      .then(res => { if (res?.url) handleUrl(res.url); })
      .catch(() => {});

    return () => { listenerHandle?.remove(); };
  });
</script>

{@render children()}
