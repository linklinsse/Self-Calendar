package app.selfcalendar.app.widget

import android.appwidget.AppWidgetManager
import android.content.ComponentName
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

@CapacitorPlugin(name = "WidgetBridge")
class WidgetBridgePlugin : Plugin() {

    @PluginMethod
    fun updateTheme(call: PluginCall) {
        val themeJson = call.getString("theme") ?: "{}"
        val prefs = context.getSharedPreferences("widget_data", android.content.Context.MODE_PRIVATE)
        prefs.edit().putString("theme", themeJson).apply()

        // Theme doesn't change what data exists — just re-render with
        // whatever's cached, no need to hit the API again.
        renderAllWidgets()
        call.resolve()
    }

    /**
     * Pushes the JWT + API base URL the widget needs to fetch its own data
     * (see WidgetDataFetcher). Called on login/logout — an empty token
     * means logged out, in which case cached events are cleared instead of
     * being left visible indefinitely.
     *
     * Capacitor dispatches @PluginMethod calls off the main thread, so the
     * blocking network fetch triggered here is safe to run inline.
     */
    @PluginMethod
    fun updateAuth(call: PluginCall) {
        val token = call.getString("token") ?: ""
        val refreshToken = call.getString("refreshToken") ?: ""
        val apiBaseUrl = call.getString("apiBaseUrl") ?: ""

        if (token.isBlank()) {
            // Signed out — drop the refresh token too, or the widget could
            // mint itself a fresh access token and keep showing data for a
            // signed-out account.
            TokenStore.clear(context)
        } else {
            TokenStore.save(context, token)
            // Absent on an older app build or if minting failed; keep any
            // existing one rather than wiping a still-valid refresh token.
            if (refreshToken.isNotBlank()) {
                TokenStore.saveRefreshToken(context, refreshToken)
            }
        }
        val prefs = context.getSharedPreferences("widget_data", android.content.Context.MODE_PRIVATE)
        val editor = prefs.edit()
        editor.putString("api_base_url", apiBaseUrl)
        // Clean up the plaintext token this file may still hold from a
        // previous app version, now that it's only ever stored via TokenStore.
        editor.remove("auth_token")
        if (token.isBlank()) {
            editor.putString("events", "[]")
        }
        editor.apply()

        val mgr = AppWidgetManager.getInstance(context)
        val ids = mgr.getAppWidgetIds(ComponentName(context, MonthWidgetProvider::class.java))
        for (id in ids) {
            MonthWidgetProvider.updateWidget(context, mgr, id)
            if (token.isNotBlank()) {
                MonthWidgetProvider.refreshWidgetDataAndRender(context, mgr, id)
            }
        }
        call.resolve()
    }

    private fun renderAllWidgets() {
        val mgr = AppWidgetManager.getInstance(context)
        val ids = mgr.getAppWidgetIds(ComponentName(context, MonthWidgetProvider::class.java))
        for (id in ids) MonthWidgetProvider.updateWidget(context, mgr, id)
    }
}
