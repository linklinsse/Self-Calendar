import { registerPlugin, Capacitor } from '@capacitor/core';
import { visibleEvents } from './stores/index.js';
import { expandEventsForRange } from './utils.js';

const WidgetBridge = registerPlugin('WidgetBridge');

export function initWidgetSync() {
  if (!Capacitor.isNativePlatform()) return;

  visibleEvents.subscribe(async (events) => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 2, 0);
    const occs = expandEventsForRange(events, start, end);

    const payload = occs.map(o => ({
      date: o.startDate.toISOString().slice(0, 10),
      color: o.ev.color
    }));

    try {
      await WidgetBridge.updateEvents({ events: JSON.stringify(payload) });
    } catch (e) {
      // not on native or plugin not ready yet — ignore
    }
  });
}
