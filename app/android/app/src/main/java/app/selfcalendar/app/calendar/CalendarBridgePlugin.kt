package app.selfcalendar.app.calendar

import android.content.Intent
import android.provider.CalendarContract
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

/**
 * Hands an event to whatever calendar app the user has, via
 * CalendarContract's ACTION_INSERT intent.
 *
 * Deliberately uses the *intent*, not a direct write to the calendar
 * provider. The intent opens the system event editor prefilled and lets the
 * user pick the target calendar and confirm; a direct write would need
 * READ_CALENDAR/WRITE_CALENDAR runtime permissions, force us to guess which
 * of the user's calendars to write into, and give Self Calendar the ability
 * to silently modify their calendar data. The intent needs no permissions at
 * all, and the user stays in control of what lands where.
 *
 * The tradeoff is that we get no confirmation of what the user did — the
 * intent returns nothing useful, so resolve() here means "the editor
 * opened", not "an event was created". The JS side says so in its own
 * wording rather than claiming success.
 */
@CapacitorPlugin(name = "CalendarBridge")
class CalendarBridgePlugin : Plugin() {

    /**
     * Opens the system calendar's new-event editor, prefilled.
     *
     * Expected call data:
     *   title       String
     *   description String   (Self Calendar puts its deep link in here)
     *   location    String
     *   startMs     Long     epoch millis
     *   endMs       Long     epoch millis
     *   allDay      Boolean
     *   rrule       String   RFC 5545 RRULE, without the "RRULE:" prefix
     */
    @PluginMethod
    fun createEvent(call: PluginCall) {
        val startMs = call.getLong("startMs")
        val endMs = call.getLong("endMs")
        if (startMs == null || endMs == null) {
            call.reject("startMs and endMs are required")
            return
        }

        val intent = Intent(Intent.ACTION_INSERT).apply {
            data = CalendarContract.Events.CONTENT_URI
            putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, startMs)
            putExtra(CalendarContract.EXTRA_EVENT_END_TIME, endMs)
            putExtra(CalendarContract.EXTRA_EVENT_ALL_DAY, call.getBoolean("allDay", false))

            call.getString("title")?.takeIf { it.isNotBlank() }
                ?.let { putExtra(CalendarContract.Events.TITLE, it) }
            call.getString("description")?.takeIf { it.isNotBlank() }
                ?.let { putExtra(CalendarContract.Events.DESCRIPTION, it) }
            call.getString("location")?.takeIf { it.isNotBlank() }
                ?.let { putExtra(CalendarContract.Events.EVENT_LOCATION, it) }
            call.getString("rrule")?.takeIf { it.isNotBlank() }
                ?.let { putExtra(CalendarContract.Events.RRULE, it) }

            // The plugin context is not an Activity, so the new task flag is
            // required or the launch throws.
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

        // A device with no calendar app installed is unusual but real
        // (stripped ROMs, work profiles, some Android TV builds).
        // resolveActivity returning null is the documented way to detect it,
        // and an unguarded startActivity would throw
        // ActivityNotFoundException straight through the bridge.
        if (intent.resolveActivity(context.packageManager) == null) {
            call.reject("NO_CALENDAR_APP")
            return
        }

        try {
            context.startActivity(intent)
        } catch (e: Exception) {
            call.reject("Could not open the calendar app: ${e.message}", e)
            return
        }

        // "The editor opened", not "an event was created" — see the class
        // docstring. There is no callback from the system editor.
        call.resolve(JSObject().put("opened", true))
    }

    /**
     * Whether a calendar app is present to receive the intent, so the UI can
     * hide the action instead of offering a button that can only fail.
     */
    @PluginMethod
    fun isAvailable(call: PluginCall) {
        val intent = Intent(Intent.ACTION_INSERT).apply {
            data = CalendarContract.Events.CONTENT_URI
        }
        val available = intent.resolveActivity(context.packageManager) != null
        call.resolve(JSObject().put("available", available))
    }
}
