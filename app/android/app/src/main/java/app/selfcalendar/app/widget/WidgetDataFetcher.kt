package app.selfcalendar.app.widget

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/**
 * Fetches the widget's own data directly from the Self Calendar API,
 * independent of the app's in-memory/view-scoped state (which used to be
 * pushed from the WebView via WidgetBridgePlugin.updateEvents — that broke
 * whenever the app navigated to a narrower view, e.g. Day view, since it
 * only ever mirrored whatever the app's `visibleEvents` store currently
 * held). The app now only pushes its theme and auth (see updateTheme /
 * updateAuth in WidgetBridgePlugin) — this file does everything else.
 */
private const val DEFAULT_EVENT_COLOR = "#F4B8C8"
private const val HTTP_TIMEOUT_MS = 6000

/** One event as returned by GET /event/range, before per-day expansion. */
private data class ApiEvent(
    val title: String,
    val dateStart: Long, // unix seconds
    val dateEnd: Long,
    val categoryId: String?,
    val recurrence: ApiRecurrence?,
)

/** Mirrors ObjEventRecurenceSchemaComplete's wire shape. */
private data class ApiRecurrence(
    val type: String,      // D | W | M | Y
    val interval: Int,
    val days: String?,     // 7-char Monday-first bitmask, weekly only
    val endType: String,   // N | C | U
    val count: Int?,
    val until: Long?,      // unix seconds
    val exceptionDates: List<Long>, // unix seconds, midnight of the skipped occurrence
)

object WidgetDataFetcher {

    /**
     * Fetches every calendar the user can see, their categories (for event
     * colors), and events overlapping [gridStart, gridEnd], then expands
     * recurring events into per-day occurrences.
     *
     * Returns null on any failure (no token synced yet, network error,
     * expired token, ...) so the caller can keep showing its last good
     * cached render instead of clearing the widget.
     */
    fun fetchWidgetData(context: Context, gridStart: Calendar, gridEnd: Calendar): Map<String, List<WidgetEvent>>? {
        val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
        val token = prefs.getString("auth_token", null)
        val baseUrl = prefs.getString("api_base_url", null)
        if (token.isNullOrBlank() || baseUrl.isNullOrBlank()) return null

        return try {
            val calendarIds = fetchCalendarIds(baseUrl, token)
            if (calendarIds.isEmpty()) return emptyMap()

            val categoryColors = HashMap<String, String>()
            for (calId in calendarIds) {
                categoryColors.putAll(fetchCategoryColors(baseUrl, token, calId))
            }

            val fromUnix = midnight(gridStart).timeInMillis / 1000
            val toUnix = midnight(gridEnd).timeInMillis / 1000 + 86399 // include all of the last day
            val events = fetchEvents(baseUrl, token, calendarIds, fromUnix, toUnix)

            buildEventsByDate(events, categoryColors, gridStart, gridEnd)
        } catch (e: Exception) {
            null
        }
    }

    private fun buildEventsByDate(
        events: List<ApiEvent>,
        categoryColors: Map<String, String>,
        gridStart: Calendar,
        gridEnd: Calendar,
    ): Map<String, List<WidgetEvent>> {
        val isoFmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        val map = HashMap<String, MutableList<WidgetEvent>>()
        val gridStartMs = midnight(gridStart).timeInMillis
        val gridEndMs = midnight(gridEnd).timeInMillis

        for (ev in events) {
            val color = ev.categoryId?.let { categoryColors[it] } ?: DEFAULT_EVENT_COLOR
            val allDay = (ev.dateEnd - ev.dateStart) % 86400L == 0L
            val s = unixToCalendar(ev.dateStart)
            val e = unixToCalendar(ev.dateEnd)
            val spanMs = midnight(e).timeInMillis - midnight(s).timeInMillis
            val spanDays = (spanMs / 86_400_000L).toInt() // 0 = single day, N = spans N+1 days

            val occurrenceStarts: List<Calendar> = if (ev.recurrence == null) {
                if (midnight(e).timeInMillis >= gridStartMs && midnight(s).timeInMillis <= gridEndMs) {
                    listOf(s)
                } else emptyList()
            } else {
                val exceptions = ev.recurrence.exceptionDates
                    .map { midnight(unixToCalendar(it)).timeInMillis }
                    .toSet()
                occurrencesInRange(s, spanMs, ev.recurrence, gridStart, gridEnd)
                    .filter { midnight(it).timeInMillis !in exceptions }
            }

            for (occStart in occurrenceStarts) {
                val startMinutes = if (allDay) null
                    else occStart.get(Calendar.HOUR_OF_DAY) * 60 + occStart.get(Calendar.MINUTE)

                // Place the event on every day it spans (clipped to the
                // grid), not just its first day — a per-day list can't draw
                // a connected banner the way MonthView.svelte does, but a
                // multi-day event should still show up on every day it
                // actually covers rather than disappearing after day one.
                var dayCursor = midnight(occStart)
                for (d in 0..spanDays) {
                    if (dayCursor.timeInMillis in gridStartMs..gridEndMs) {
                        val dateStr = isoFmt.format(dayCursor.time)
                        map.getOrPut(dateStr) { mutableListOf() }
                            .add(WidgetEvent(ev.title, color, allDay, startMinutes))
                    }
                    dayCursor = (dayCursor.clone() as Calendar).apply { add(Calendar.DAY_OF_MONTH, 1) }
                }
            }
        }

        for (list in map.values) {
            list.sortWith(compareBy({ !it.allDay }, { it.startMinutes ?: Int.MAX_VALUE }))
        }
        return map
    }

    // ── Recurrence expansion — a direct port of getOccurrencesInRange /
    // _nextOccurrence from app/src/lib/utils.js, operating on the API's
    // wire-format recurrence fields instead of the JS-internal format. ──

    private fun occurrencesInRange(
        baseStart: Calendar,
        spanMs: Long,
        rec: ApiRecurrence,
        rangeStart: Calendar,
        rangeEnd: Calendar,
    ): List<Calendar> {
        val results = mutableListOf<Calendar>()
        var cur = baseStart.clone() as Calendar
        var count = 0
        val rangeEndMidnight = midnight(rangeEnd).timeInMillis
        val rangeStartMidnight = midnight(rangeStart).timeInMillis
        val untilMidnight = rec.until?.let { midnight(unixToCalendar(it)).timeInMillis }

        for (iter in 0 until 1500) { // safety cap, matches the JS port
            if (rec.endType == "U" && untilMidnight != null && midnight(cur).timeInMillis > untilMidnight) break
            if (rec.endType == "C" && rec.count != null && count >= rec.count) break
            if (midnight(cur).timeInMillis > rangeEndMidnight) break

            val occEnd = (cur.clone() as Calendar).apply { timeInMillis += spanMs }
            if (midnight(occEnd).timeInMillis >= rangeStartMidnight) {
                results.add(cur.clone() as Calendar)
            }
            count++

            val next = nextOccurrence(cur, rec) ?: break
            cur = next
        }
        return results
    }

    private fun nextOccurrence(current: Calendar, rec: ApiRecurrence): Calendar? {
        val d = current.clone() as Calendar
        val interval = maxOf(1, rec.interval)

        return when (rec.type) {
            "D" -> { d.add(Calendar.DAY_OF_MONTH, interval); d }
            "W" -> {
                val days = parseDaysBitmask(rec.days)
                if (days.isNotEmpty()) {
                    val sorted = days.sorted()
                    val curDow = d.get(Calendar.DAY_OF_WEEK) - 1 // Calendar Sun=1..Sat=7 -> 0..6
                    val nextDow = sorted.firstOrNull { it > curDow }
                    if (nextDow != null) {
                        d.add(Calendar.DAY_OF_MONTH, nextDow - curDow)
                    } else {
                        d.add(Calendar.DAY_OF_MONTH, (7 - curDow + sorted[0]) + (interval - 1) * 7)
                    }
                } else {
                    d.add(Calendar.DAY_OF_MONTH, 7 * interval)
                }
                d
            }
            "M" -> { d.add(Calendar.MONTH, interval); d }
            "Y" -> { d.add(Calendar.YEAR, interval); d }
            else -> null
        }
    }

    /** API days: 7-char Monday-first bitmask -> 0=Sun..6=Sat day indices. */
    private fun parseDaysBitmask(days: String?): List<Int> {
        if (days == null || days.length != 7) return emptyList()
        val result = mutableListOf<Int>()
        for (i in 0 until 7) {
            if (days[i] == '1') result.add((i + 1) % 7)
        }
        return result
    }

    private fun midnight(cal: Calendar): Calendar {
        val c = cal.clone() as Calendar
        c.set(Calendar.HOUR_OF_DAY, 0)
        c.set(Calendar.MINUTE, 0)
        c.set(Calendar.SECOND, 0)
        c.set(Calendar.MILLISECOND, 0)
        return c
    }

    private fun unixToCalendar(unixSeconds: Long): Calendar {
        val c = Calendar.getInstance()
        c.timeInMillis = unixSeconds * 1000
        return c
    }

    // ── HTTP + JSON ──────────────────────────────────────────────────────

    private fun fetchCalendarIds(baseUrl: String, token: String): List<String> {
        val json = httpGet("${baseUrl.trimEnd('/')}/calendar/", token)
        val arr = JSONArray(json)
        return (0 until arr.length()).map { arr.getJSONObject(it).getString("id") }
    }

    private fun fetchCategoryColors(baseUrl: String, token: String, calendarId: String): Map<String, String> {
        val encodedId = URLEncoder.encode(calendarId, "UTF-8")
        val json = httpGet("${baseUrl.trimEnd('/')}/category/calendar/$encodedId", token)
        val arr = JSONArray(json)
        val map = HashMap<String, String>()
        for (i in 0 until arr.length()) {
            val obj = arr.getJSONObject(i)
            // isNull() treats both "missing" and JSON null as "no color" —
            // optString(key, fallback) can return the literal string "null"
            // instead of the fallback when the value is JSON null.
            val color = if (obj.isNull("color")) DEFAULT_EVENT_COLOR else obj.getString("color")
            map[obj.getString("id")] = color
        }
        return map
    }

    private fun fetchEvents(baseUrl: String, token: String, calendarIds: List<String>, fromUnix: Long, toUnix: Long): List<ApiEvent> {
        val url = StringBuilder(baseUrl.trimEnd('/'))
        url.append("/event/range?from_date=").append(fromUnix).append("&to_date=").append(toUnix)
        for (id in calendarIds) url.append("&calendar_ids=").append(URLEncoder.encode(id, "UTF-8"))

        val json = httpGet(url.toString(), token)
        val arr = JSONArray(json)
        val result = mutableListOf<ApiEvent>()
        for (i in 0 until arr.length()) {
            val obj = arr.getJSONObject(i)
            val recObj = if (obj.isNull("obj_recurence")) null else obj.optJSONObject("obj_recurence")
            result.add(
                ApiEvent(
                    title = obj.optString("title", ""),
                    dateStart = obj.getLong("date_start"),
                    dateEnd = obj.getLong("date_end"),
                    categoryId = if (obj.isNull("category_id")) null else obj.getString("category_id"),
                    recurrence = recObj?.let { parseApiRecurrence(it) },
                )
            )
        }
        return result
    }

    private fun parseApiRecurrence(obj: JSONObject): ApiRecurrence {
        val exceptions = mutableListOf<Long>()
        val exceptionsArr = obj.optJSONArray("obj_exceptions")
        if (exceptionsArr != null) {
            for (i in 0 until exceptionsArr.length()) {
                exceptions.add(exceptionsArr.getJSONObject(i).getLong("date"))
            }
        }
        return ApiRecurrence(
            type = obj.optString("type", "D"),
            interval = obj.optInt("interval", 1),
            days = if (obj.isNull("days")) null else obj.getString("days"),
            endType = obj.optString("endType", "N"),
            count = if (obj.isNull("count")) null else obj.getInt("count"),
            until = if (obj.isNull("until")) null else obj.getLong("until"),
            exceptionDates = exceptions,
        )
    }

    private fun httpGet(urlStr: String, token: String): String {
        val conn = URL(urlStr).openConnection() as HttpURLConnection
        try {
            conn.requestMethod = "GET"
            conn.setRequestProperty("Authorization", "Bearer $token")
            conn.connectTimeout = HTTP_TIMEOUT_MS
            conn.readTimeout = HTTP_TIMEOUT_MS
            val code = conn.responseCode
            if (code !in 200..299) throw java.io.IOException("HTTP $code for $urlStr")
            return conn.inputStream.bufferedReader().use { it.readText() }
        } finally {
            conn.disconnect()
        }
    }
}
