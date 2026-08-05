import { registerPlugin, Capacitor } from '@capacitor/core';
import { currentUser } from './stores/index.js';
import { activeThemeId, resolveTheme } from './themes/index.js';
import { getToken } from './services/api.js';
import { fetchRefreshToken } from './services/auth.service.js';
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
/**
 * Push the current token (or an empty one, meaning signed out) to the widget.
 *
 * Exported because the widget holds its *own* copy of the JWT and has no way
 * to notice that the app's has changed. Anything that replaces the token
 * without going through a `currentUser` transition — a password change, a
 * silent refresh — has to call this or the widget keeps using a dead token
 * and silently shows stale data.
 */
export async function syncWidgetAuth() {
  if (!Capacitor.isNativePlatform()) return;

  const token = getToken() ?? '';
  // Only worth minting one when there is a session to mint it for, and only
  // on native — the widget is the sole consumer.
  const refreshToken = token ? (await fetchRefreshToken()) ?? '' : '';

  try {
    await WidgetBridge.updateAuth({
      token,
      refreshToken,
      apiBaseUrl: API_BASE_URL,
    });
  } catch {
    // not on native or plugin not ready yet — ignore
  }
}

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
    if (!user) {
      try {
        // Empty token means signed out; the plugin clears the refresh token
        // too, so the widget can't renew itself for a signed-out account.
        await WidgetBridge.updateAuth({
          token: '', refreshToken: '', apiBaseUrl: API_BASE_URL,
        });
      } catch { /* not on native or plugin not ready yet */ }
      return;
    }
    await syncWidgetAuth();
  });
}
