package app.selfcalendar.app.widget

import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

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
/**
 * One materialised occurrence, as returned by GET /event/range?expand=true.
 *
 * There is no recurrence rule here on purpose. The widget used to carry a
 * hand-maintained Kotlin port of the web app's recurrence expansion — a
 * third implementation of the same logic, with no tests, which drifted from
 * the others twice (monthly/yearly rollover, and exception matching). The
 * server now expands, and this file just draws what it is given.
 */
private data class ApiOccurrence(
    val title: String,
    val dateStart: Long, // unix seconds
    val dateEnd: Long,
    val categoryId: String?,
)

object WidgetDataFetcher {

    private const val TAG = "WidgetDataFetcher"


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
        val token = TokenStore.load(context)
        val baseUrl = prefs.getString("api_base_url", null)
        if (token.isNullOrBlank() || baseUrl.isNullOrBlank()) return null

        return try {
            fetchWith(context, baseUrl, token, gridStart, gridEnd)
        } catch (e: UnauthorizedException) {
            // The access token expired. The widget can go weeks without the
            // user opening the app, while an access token lasts a day, so
            // this is the normal steady state rather than an edge case —
            // before refresh tokens existed the widget simply froze on stale
            // data here, with no way back short of signing in again.
            val fresh = refreshAccessToken(context, baseUrl)
            if (fresh == null) {
                Log.w(TAG, "Token expired and refresh failed — widget is signed out")
                return null
            }
            try {
                fetchWith(context, baseUrl, fresh, gridStart, gridEnd)
            } catch (e2: Exception) {
                Log.w(TAG, "widget fetch failed after refresh", e2)
                null
            }
        } catch (e: Exception) {
            // Swallowed on purpose (caller falls back to the last good
            // cached render) — but silently is how failures here go
            // unnoticed. This is the least on-device-tested code path in
            // the app; log so a broken fetch is at least visible in logcat.
            Log.w(TAG, "widget fetch failed", e)
            null
        }
    }

    /**
     * One full fetch pass with a given access token.
     *
     * Split out of fetchWidgetData so a 401 can be retried once with a
     * refreshed token without duplicating any of this. Lets
     * UnauthorizedException propagate; every other failure is handled by the
     * caller.
     */
    private fun fetchWith(
        context: Context,
        baseUrl: String,
        token: String,
        gridStart: Calendar,
        gridEnd: Calendar,
    ): Map<String, List<WidgetEvent>>? {
        return run {
            val calendarIds = fetchCalendarIds(baseUrl, token)
            if (calendarIds.isEmpty()) return emptyMap()

            // One blocking HTTP call per calendar, each with its own
            // HTTP_TIMEOUT_MS — sequentially that's a potential
            // calendarIds.size * HTTP_TIMEOUT_MS widget refresh. Fetch them
            // concurrently instead (already running on a background thread
            // via goAsync(), so this doesn't touch the main thread).
            val categoryColors = HashMap<String, String>()
            if (calendarIds.isNotEmpty()) {
                val executor = Executors.newFixedThreadPool(minOf(calendarIds.size, 6))
                try {
                    val futures = calendarIds.map { calId ->
                        executor.submit<Map<String, String>> { fetchCategoryColors(baseUrl, token, calId) }
                    }
                    for (future in futures) {
                        try {
                            categoryColors.putAll(
                                future.get(HTTP_TIMEOUT_MS.toLong() + 1000, TimeUnit.MILLISECONDS)
                            )
                        } catch (e: java.util.concurrent.ExecutionException) {
                            // Futures wrap the original failure, so a 401 in
                            // here arrives as ExecutionException and would
                            // otherwise miss the refresh-and-retry path.
                            val cause = e.cause
                            if (cause is UnauthorizedException) throw cause
                            throw e
                        }
                    }
                } finally {
                    executor.shutdown()
                }
            }

            val fromUnix = midnight(gridStart).timeInMillis / 1000
            val toUnix = midnight(gridEnd).timeInMillis / 1000 + 86399 // include all of the last day
            val occurrences = fetchOccurrences(baseUrl, token, calendarIds, fromUnix, toUnix)

            buildEventsByDate(occurrences, categoryColors, gridStart, gridEnd)
        }
    }

    /**
     * Bucket already-expanded occurrences by ISO date for rendering.
     *
     * No recurrence logic here any more: the server did it. This used to
     * expand rules itself via a hand-maintained Kotlin port of the web app's
     * implementation, which drifted from it twice.
     */
    private fun buildEventsByDate(
        occurrences: List<ApiOccurrence>,
        categoryColors: Map<String, String>,
        gridStart: Calendar,
        gridEnd: Calendar,
    ): Map<String, List<WidgetEvent>> {
        val isoFmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        val map = HashMap<String, MutableList<WidgetEvent>>()
        val gridStartMs = midnight(gridStart).timeInMillis
        val gridEndMs = midnight(gridEnd).timeInMillis

        for (occ in occurrences) {
            val color = occ.categoryId?.let { categoryColors[it] } ?: DEFAULT_EVENT_COLOR
            val s = unixToCalendar(occ.dateStart)
            val e = unixToCalendar(occ.dateEnd)

            // A span that's an exact multiple of 24h isn't sufficient on its
            // own — a 14:00-to-14:00-next-day timed event (or a
            // zero-duration event at a non-midnight time) would otherwise
            // also match. Require the start to actually be local midnight,
            // matching how the app itself encodes all-day events. Mirrors
            // event.service.js's deserialise() on the web app.
            val allDay = (occ.dateEnd - occ.dateStart) % 86400L == 0L &&
                occ.dateEnd >= occ.dateStart &&
                s.get(Calendar.HOUR_OF_DAY) == 0 && s.get(Calendar.MINUTE) == 0 &&
                s.get(Calendar.SECOND) == 0

            val spanMs = midnight(e).timeInMillis - midnight(s).timeInMillis
            val spanDays = (spanMs / 86_400_000L).toInt() // 0 = single day, N spans N+1

            val startMinutes = if (allDay) null
                else s.get(Calendar.HOUR_OF_DAY) * 60 + s.get(Calendar.MINUTE)

            // Place the event on every day it spans (clipped to the grid),
            // not just its first day — a per-day list can't draw a connected
            // banner the way MonthView.svelte does, but a multi-day event
            // should still show up on every day it actually covers rather
            // than disappearing after day one.
            var dayCursor = midnight(s)
            for (d in 0..spanDays) {
                if (dayCursor.timeInMillis in gridStartMs..gridEndMs) {
                    val dateStr = isoFmt.format(dayCursor.time)
                    map.getOrPut(dateStr) { mutableListOf() }
                        .add(WidgetEvent(occ.title, color, allDay, startMinutes))
                }
                dayCursor = (dayCursor.clone() as Calendar).apply {
                    add(Calendar.DAY_OF_MONTH, 1)
                }
            }
        }

        for (list in map.values) {
            list.sortWith(compareBy({ !it.allDay }, { it.startMinutes ?: Int.MAX_VALUE }))
        }
        return map
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

    /**
     * Fetch occurrences already expanded by the server.
     *
     * expand=true makes the API apply the recurrence rules and drop excluded
     * occurrences, so a recurring event arrives once per occurrence. timezone
     * is sent explicitly because events are stored as bare timestamps: the
     * server has no way to know which day boundaries to expand against, and
     * would otherwise default to UTC and shift occurrences for anyone else.
     */
    private fun fetchOccurrences(
        baseUrl: String,
        token: String,
        calendarIds: List<String>,
        fromUnix: Long,
        toUnix: Long,
    ): List<ApiOccurrence> {
        val url = StringBuilder(baseUrl.trimEnd('/'))
        url.append("/event/range?expand=true")
        url.append("&from_date=").append(fromUnix).append("&to_date=").append(toUnix)
        url.append("&timezone=").append(URLEncoder.encode(TimeZone.getDefault().id, "UTF-8"))
        for (id in calendarIds) url.append("&calendar_ids=").append(URLEncoder.encode(id, "UTF-8"))

        val json = httpGet(url.toString(), token)
        val arr = JSONArray(json)
        val result = mutableListOf<ApiOccurrence>()
        for (i in 0 until arr.length()) {
            val obj = arr.getJSONObject(i)
            val event = obj.getJSONObject("event")
            result.add(
                ApiOccurrence(
                    title = event.optString("title", ""),
                    dateStart = obj.getLong("date_start"),
                    dateEnd = obj.getLong("date_end"),
                    categoryId =
                        if (event.isNull("category_id")) null
                        else event.getString("category_id"),
                )
            )
        }
        return result
    }

    /** Thrown on a 401 so the caller can tell "token expired" from "network died". */
    private class UnauthorizedException(message: String) : java.io.IOException(message)

    private fun httpGet(urlStr: String, token: String): String {
        val conn = URL(urlStr).openConnection() as HttpURLConnection
        try {
            conn.requestMethod = "GET"
            conn.setRequestProperty("Authorization", "Bearer $token")
            conn.connectTimeout = HTTP_TIMEOUT_MS
            conn.readTimeout = HTTP_TIMEOUT_MS
            val code = conn.responseCode
            if (code == 401) throw UnauthorizedException("HTTP 401 for $urlStr")
            if (code !in 200..299) throw java.io.IOException("HTTP $code for $urlStr")
            return conn.inputStream.bufferedReader().use { it.readText() }
        } finally {
            conn.disconnect()
        }
    }

    /**
     * Exchange the stored refresh token for a fresh access token, persist it,
     * and return it. Null when there is no refresh token or the exchange
     * fails — which includes the refresh token itself having expired or been
     * invalidated by a password change, i.e. genuinely signed out.
     */
    private fun refreshAccessToken(context: Context, baseUrl: String): String? {
        val refreshToken = TokenStore.loadRefreshToken(context) ?: return null

        val conn = URL("${baseUrl.trimEnd('/')}/auth/refresh").openConnection()
            as HttpURLConnection
        try {
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.doOutput = true
            conn.connectTimeout = HTTP_TIMEOUT_MS
            conn.readTimeout = HTTP_TIMEOUT_MS

            // JSONObject rather than string interpolation: a token is opaque
            // and must not be pasted unescaped into a JSON body.
            val body = JSONObject().put("refresh_token", refreshToken).toString()
            conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }

            if (conn.responseCode !in 200..299) {
                Log.w(TAG, "Refresh failed: HTTP ${conn.responseCode}")
                return null
            }

            // /auth/refresh returns a bare JSON string, matching /auth/login.
            val raw = conn.inputStream.bufferedReader().use { it.readText() }.trim()
            val token = raw.removeSurrounding("\"")
            if (token.isBlank()) return null

            // Only the access token is replaced — the refresh token is still
            // valid and still needed.
            TokenStore.saveAccessToken(context, token)
            return token
        } catch (e: Exception) {
            Log.w(TAG, "Refresh failed", e)
            return null
        } finally {
            conn.disconnect()
        }
    }
}
