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
    fun updateEvents(call: PluginCall) {
        val eventsJson = call.getString("events") ?: "[]"
        val prefs = context.getSharedPreferences("widget_data", android.content.Context.MODE_PRIVATE)
        prefs.edit().putString("events", eventsJson).apply()

        val mgr = AppWidgetManager.getInstance(context)
        val ids = mgr.getAppWidgetIds(ComponentName(context, MonthWidgetProvider::class.java))
        for (id in ids) MonthWidgetProvider.updateWidget(context, mgr, id)

        call.resolve()
    }
}
