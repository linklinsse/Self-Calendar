import { registerPlugin, Capacitor } from '@capacitor/core';
import { currentUser } from './stores/index.js';
import { activeThemeId, resolveTheme } from './themes/index.js';
import { getToken } from './services/api.js';
import { API_BASE_URL } from './config.js';

const WidgetBridge = registerPlugin('WidgetBridge');

/**
 * Keeps the native Android home-screen widget in sync with the app's
 * *theme* and *credentials* only. Events are deliberately NOT pushed from
 * here — the widget used to mirror the app's `visibleEvents` store, which
 * is scoped to whatever view is currently open (e.g. narrows to a single
 * day in Day view), so switching views in the app made the widget appear
 * to "lose" events. The widget now fetches its own events straight from
 * the API on its own schedule (see WidgetDataFetcher.kt), independent of
 * anything happening in the app's UI.
 */
export function initWidgetSync() {
  if (!Capacitor.isNativePlatform()) return;

  activeThemeId.subscribe(async (id) => {
    const theme = resolveTheme(id);
    const payload = {
      bg:        theme.bgSurface,
      text:      theme.text1,
      textMuted: theme.text2,
      accent:    theme.accent,
    };

    try {
      await WidgetBridge.updateTheme({ theme: JSON.stringify(payload) });
    } catch (e) {
      // not on native or plugin not ready yet — ignore
    }
  });

  currentUser.subscribe(async (user) => {
    try {
      await WidgetBridge.updateAuth({
        token: user ? (getToken() ?? '') : '',
        apiBaseUrl: API_BASE_URL,
      });
    } catch (e) {
      // not on native or plugin not ready yet — ignore
    }
  });
}
