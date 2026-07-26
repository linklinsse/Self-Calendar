package app.selfcalendar.app.widget

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.net.Uri
import android.app.PendingIntent
import android.view.View
import android.widget.RemoteViews
import app.selfcalendar.app.R
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/**
 * One event occurrence on a given day. Built natively by WidgetDataFetcher
 * from the API's own /event/range + /category responses (not pushed from
 * the app anymore — see WidgetDataFetcher.kt for why). Not private: shared
 * with WidgetDataFetcher.kt via same-package visibility.
 */
data class WidgetEvent(
    val title: String,
    val color: String,
    val allDay: Boolean,
    val startMinutes: Int?, // null for all-day / unparseable "HH:MM"
)

/**
 * The app's currently selected theme, as pushed from WidgetBridgePlugin
 * (see lib/widgetSync.js and the theme files under lib/themes on the JS
 * side). Only the handful of colors the widget actually renders with.
 */
private data class WidgetTheme(
    val bg: Int,
    val text: Int,
    val textMuted: Int,
    val accent: Int,
)

class MonthWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, mgr: AppWidgetManager, ids: IntArray) {
        // Instant render from whatever's cached, then refresh from the API
        // in the background — onUpdate also fires periodically
        // (updatePeriodMillis in month_widget_info.xml), which is the
        // widget's regular polling refresh.
        for (id in ids) updateWidget(context, mgr, id)

        val pending = goAsync()
        Thread {
            try {
                for (id in ids) refreshWidgetDataAndRender(context, mgr, id)
            } finally {
                pending.finish()
            }
        }.start()
    }

    override fun onDeleted(context: Context, appWidgetIds: IntArray) {
        val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
        val editor = prefs.edit()
        for (id in appWidgetIds) editor.remove(PREF_OFFSET_PREFIX + id)
        editor.apply()
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)

        if (intent.action != ACTION_PREV_MONTH && intent.action != ACTION_NEXT_MONTH) return

        val widgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, -1)
        if (widgetId == -1) return

        val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
        val key = PREF_OFFSET_PREFIX + widgetId
        val delta = if (intent.action == ACTION_NEXT_MONTH) 1 else -1
        prefs.edit().putInt(key, prefs.getInt(key, 0) + delta).apply()

        val mgr = AppWidgetManager.getInstance(context)
        // Instant render for the new month using whatever's cached (likely
        // stale for this month until the fetch below lands), then fetch
        // that month's events for real.
        updateWidget(context, mgr, widgetId)

        val pending = goAsync()
        Thread {
            try {
                refreshWidgetDataAndRender(context, mgr, widgetId)
            } finally {
                pending.finish()
            }
        }.start()
    }

    companion object {
        private const val ACTION_PREV_MONTH = "app.selfcalendar.app.widget.ACTION_PREV_MONTH"
        private const val ACTION_NEXT_MONTH = "app.selfcalendar.app.widget.ACTION_NEXT_MONTH"
        private const val PREF_OFFSET_PREFIX = "month_offset_"

        // Total event cards (all-day + timed) shown per day cell before
        // collapsing the rest into a "+N" indicator — mirrors the main
        // app's month view (MonthView.svelte's totalShown logic).
        private const val MAX_SHOWN_PER_DAY = 3

        // Text color used *on top of* the today-circle's accent background —
        // fixed dark, not theme-driven, matching the app's own CSS
        // (.cell.today .cell-num always uses #1a0812) since every theme's
        // accent color is a light/pastel tone that dark text reads well on.
        private val TODAY_TEXT_COLOR = Color.parseColor("#1A0812")

        // Bitmap sizes are arbitrary fixed resolutions, not device-exact —
        // ImageView scales them to fit, and a flat-color rounded shape
        // stretches without visible artifacts.
        private const val BG_BITMAP_SIZE = 300
        private const val TODAY_CIRCLE_BITMAP_SIZE = 96

        private val DEFAULT_THEME = WidgetTheme(
            bg = Color.parseColor("#13131a"),
            text = Color.parseColor("#f0eaf2"),
            textMuted = Color.parseColor("#a090a4"),
            accent = Color.parseColor("#f4b8c8"),
        )

        private val DOW_IDS = listOf(
            R.id.dow_1, R.id.dow_2, R.id.dow_3, R.id.dow_4, R.id.dow_5, R.id.dow_6, R.id.dow_7
        )

        // Fixed event "slots" declared statically in month_widget_cell.xml —
        // see the comment at the top of that file for why these aren't
        // built dynamically with RemoteViews#addView() per event.
        private val EVENT_ROW_IDS = listOf(R.id.event_row_1, R.id.event_row_2, R.id.event_row_3)
        private val EVENT_ACCENT_IDS = listOf(R.id.event_accent_1, R.id.event_accent_2, R.id.event_accent_3)
        private val EVENT_TITLE_IDS = listOf(R.id.event_title_1, R.id.event_title_2, R.id.event_title_3)

        private val ISO = SimpleDateFormat("yyyy-MM-dd", Locale.US)

        fun updateWidget(context: Context, mgr: AppWidgetManager, widgetId: Int) {
            val pkg = context.packageName
            val root = RemoteViews(pkg, R.layout.month_widget)

            val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val eventsJson = prefs.getString("events", "[]") ?: "[]"
            val eventsByDate = parseEvents(eventsJson)
            val theme = parseTheme(prefs.getString("theme", null))
            val monthOffset = prefs.getInt(PREF_OFFSET_PREFIX + widgetId, 0)

            val anchor = Calendar.getInstance()
            anchor.add(Calendar.MONTH, monthOffset)

            val monthTitleFmt = SimpleDateFormat("MMMM yyyy", Locale.getDefault())
            root.setTextViewText(R.id.month_title, monthTitleFmt.format(anchor.time))

            root.setImageViewBitmap(R.id.widget_bg_image, roundedRectBitmap(BG_BITMAP_SIZE, theme.bg))
            root.setTextColor(R.id.month_title, theme.text)
            root.setTextColor(R.id.btn_prev_month, theme.text)
            root.setTextColor(R.id.btn_next_month, theme.text)
            for (dowId in DOW_IDS) root.setTextColor(dowId, theme.textMuted)

            root.setOnClickPendingIntent(R.id.btn_prev_month, navPendingIntent(context, widgetId, ACTION_PREV_MONTH))
            root.setOnClickPendingIntent(R.id.btn_next_month, navPendingIntent(context, widgetId, ACTION_NEXT_MONTH))

            root.removeAllViews(R.id.days_container)

            val grid = buildMonthGrid(anchor.get(Calendar.YEAR), anchor.get(Calendar.MONTH))
            val currentMonth = anchor.get(Calendar.MONTH)

            for (week in 0 until 6) {
                val rowView = RemoteViews(pkg, R.layout.month_widget_row)
                for (col in 0 until 7) {
                    val day = grid[week * 7 + col]
                    val cell = buildCell(context, pkg, day, currentMonth, eventsByDate, theme, widgetId * 100 + week * 7 + col)
                    rowView.addView(R.id.week_row, cell)
                }
                root.addView(R.id.days_container, rowView)
            }

            mgr.updateAppWidget(widgetId, root)
        }

        /**
         * Fetches this widget's currently-displayed month from the API
         * (blocking — call off the main thread), caches the result, and
         * re-renders. No-ops (keeps whatever was last cached) on any
         * failure — no auth synced yet, network error, expired token, etc.
         */
        fun refreshWidgetDataAndRender(context: Context, mgr: AppWidgetManager, widgetId: Int) {
            val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val monthOffset = prefs.getInt(PREF_OFFSET_PREFIX + widgetId, 0)
            val anchor = Calendar.getInstance()
            anchor.add(Calendar.MONTH, monthOffset)
            val grid = buildMonthGrid(anchor.get(Calendar.YEAR), anchor.get(Calendar.MONTH))

            val fresh = WidgetDataFetcher.fetchWidgetData(context, grid.first(), grid.last()) ?: return
            prefs.edit().putString("events", serializeEventsCache(fresh)).apply()
            updateWidget(context, mgr, widgetId)
        }

        /** Serializes fetched events back into the same flat JSON shape
         * parseEvents() reads, so updateWidget()'s cache-based render path
         * doesn't need to know whether the cache came from a fetch. */
        private fun serializeEventsCache(eventsByDate: Map<String, List<WidgetEvent>>): String {
            val arr = JSONArray()
            for ((date, list) in eventsByDate) {
                for (ev in list) {
                    val obj = JSONObject()
                    obj.put("date", date)
                    obj.put("color", ev.color)
                    obj.put("title", ev.title)
                    obj.put("allDay", ev.allDay)
                    if (ev.startMinutes != null) {
                        val h = ev.startMinutes / 60
                        val m = ev.startMinutes % 60
                        obj.put("start", String.format(Locale.US, "%02d:%02d", h, m))
                    } else {
                        obj.put("start", JSONObject.NULL)
                    }
                    arr.put(obj)
                }
            }
            return arr.toString()
        }

        private fun navPendingIntent(context: Context, widgetId: Int, action: String): PendingIntent {
            val intent = Intent(context, MonthWidgetProvider::class.java).apply {
                this.action = action
                putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId)
            }
            // requestCode must be unique per (widgetId, action) pair, otherwise
            // FLAG_UPDATE_CURRENT would make prev/next share one PendingIntent.
            val requestCode = widgetId * 10 + (if (action == ACTION_NEXT_MONTH) 1 else 0)
            return PendingIntent.getBroadcast(
                context, requestCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }

        private fun buildCell(
            context: Context,
            pkg: String,
            day: Calendar,
            currentMonth: Int,
            eventsByDate: Map<String, List<WidgetEvent>>,
            theme: WidgetTheme,
            requestCode: Int
        ): RemoteViews {
            val cell = RemoteViews(pkg, R.layout.month_widget_cell)
            val dateStr = ISO.format(day.time)
            val isToday = isSameDay(day, Calendar.getInstance())
            val isOutside = day.get(Calendar.MONTH) != currentMonth

            cell.setTextViewText(R.id.day_number, day.get(Calendar.DAY_OF_MONTH).toString())

            if (isToday) {
                cell.setImageViewBitmap(R.id.day_number_bg, circleBitmap(TODAY_CIRCLE_BITMAP_SIZE, theme.accent))
                cell.setTextColor(R.id.day_number, TODAY_TEXT_COLOR)
            } else {
                cell.setImageViewResource(R.id.day_number_bg, 0)
                cell.setTextColor(R.id.day_number, if (isOutside) theme.textMuted else theme.text)
            }

            val dayEvents = eventsByDate[dateStr].orEmpty()
            val shown = dayEvents.take(MAX_SHOWN_PER_DAY)
            for (i in EVENT_ROW_IDS.indices) {
                if (i < shown.size) {
                    val ev = shown[i]
                    cell.setViewVisibility(EVENT_ROW_IDS[i], View.VISIBLE)
                    cell.setTextViewText(EVENT_TITLE_IDS[i], ev.title)

                    val evColor = try { Color.parseColor(ev.color) } catch (e: Exception) { Color.GRAY }
                    if (ev.allDay) {
                        // Mirrors .ev-pill--allday: solid fill, fixed dark text, no border.
                        cell.setInt(EVENT_ROW_IDS[i], "setBackgroundColor", evColor)
                        cell.setViewVisibility(EVENT_ACCENT_IDS[i], View.GONE)
                        cell.setTextColor(EVENT_TITLE_IDS[i], TODAY_TEXT_COLOR)
                    } else {
                        // Mirrors .ev-pill: ~26% tinted fill (CSS `color42`),
                        // color text, colored left accent bar.
                        cell.setInt(EVENT_ROW_IDS[i], "setBackgroundColor", withAlpha(evColor, 0x42))
                        cell.setViewVisibility(EVENT_ACCENT_IDS[i], View.VISIBLE)
                        cell.setInt(EVENT_ACCENT_IDS[i], "setColorFilter", evColor)
                        cell.setTextColor(EVENT_TITLE_IDS[i], evColor)
                    }
                } else {
                    cell.setViewVisibility(EVENT_ROW_IDS[i], View.GONE)
                }
            }
            val remaining = dayEvents.size - shown.size
            if (remaining > 0) {
                cell.setViewVisibility(R.id.overflow_text, View.VISIBLE)
                cell.setTextViewText(R.id.overflow_text, "+$remaining")
                cell.setTextColor(R.id.overflow_text, theme.textMuted)
            } else {
                cell.setViewVisibility(R.id.overflow_text, View.GONE)
            }

            val uri = Uri.parse("selfcalendar://day?date=$dateStr")
            val intent = Intent(Intent.ACTION_VIEW, uri, context, Class.forName("app.selfcalendar.app.MainActivity"))
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            val pending = PendingIntent.getActivity(
                context, requestCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            cell.setOnClickPendingIntent(R.id.cell_root, pending)

            return cell
        }

        /** Parse "HH:MM" into minutes-since-midnight, or null if absent/malformed. */
        private fun parseStartMinutes(start: String?): Int? {
            if (start.isNullOrBlank()) return null
            val parts = start.split(":")
            if (parts.size != 2) return null
            val h = parts[0].toIntOrNull() ?: return null
            val m = parts[1].toIntOrNull() ?: return null
            return h * 60 + m
        }

        private fun parseEvents(json: String): Map<String, List<WidgetEvent>> {
            val map = HashMap<String, MutableList<WidgetEvent>>()
            try {
                val arr = JSONArray(json)
                for (i in 0 until arr.length()) {
                    val obj = arr.getJSONObject(i)
                    val date = obj.getString("date")
                    val color = obj.optString("color", "#F4B8C8")
                    val title = obj.optString("title", "")
                    val allDay = obj.optBoolean("allDay", false)
                    // isNull() treats both "missing" and JSON null as "no time" —
                    // optString(key, fallback) is unreliable for a JSON-null value.
                    val startMinutes = if (allDay || obj.isNull("start")) null
                        else parseStartMinutes(obj.optString("start"))
                    map.getOrPut(date) { mutableListOf() }
                        .add(WidgetEvent(title, color, allDay, startMinutes))
                }
            } catch (e: Exception) { }

            // All-day events first, then timed events ordered by start time
            // (events with no parseable time sort last) — matches the main
            // app's month view ordering.
            for (list in map.values) {
                list.sortWith(compareBy({ !it.allDay }, { it.startMinutes ?: Int.MAX_VALUE }))
            }
            return map
        }

        /** Parse the theme JSON pushed from lib/widgetSync.js, falling back to
         * DEFAULT_THEME (matching the app's own default theme, blushNoir) if
         * nothing has synced yet or a color fails to parse. */
        private fun parseTheme(json: String?): WidgetTheme {
            if (json == null) return DEFAULT_THEME
            return try {
                val obj = JSONObject(json)
                WidgetTheme(
                    bg = Color.parseColor(obj.getString("bg")),
                    text = Color.parseColor(obj.getString("text")),
                    textMuted = Color.parseColor(obj.getString("textMuted")),
                    accent = Color.parseColor(obj.getString("accent")),
                )
            } catch (e: Exception) {
                DEFAULT_THEME
            }
        }

        private fun roundedRectBitmap(sizePx: Int, color: Int): Bitmap {
            val bmp = Bitmap.createBitmap(sizePx, sizePx, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bmp)
            val paint = Paint(Paint.ANTI_ALIAS_FLAG)
            paint.color = color
            val radius = sizePx * 0.064f // matches the old drawable's 16dp / 250dp ratio
            canvas.drawRoundRect(RectF(0f, 0f, sizePx.toFloat(), sizePx.toFloat()), radius, radius, paint)
            return bmp
        }

        private fun circleBitmap(sizePx: Int, color: Int): Bitmap {
            val bmp = Bitmap.createBitmap(sizePx, sizePx, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bmp)
            val paint = Paint(Paint.ANTI_ALIAS_FLAG)
            paint.color = color
            val r = sizePx / 2f
            canvas.drawCircle(r, r, r, paint)
            return bmp
        }

        /** Same color with a new alpha byte (0-255) — e.g. the CSS `color42` (~26%) tint used for timed-event pills. */
        private fun withAlpha(color: Int, alpha: Int): Int {
            return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color))
        }

        private fun isSameDay(a: Calendar, b: Calendar): Boolean {
            return a.get(Calendar.YEAR) == b.get(Calendar.YEAR) &&
                   a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)
        }

        private fun buildMonthGrid(year: Int, month: Int): List<Calendar> {
            val cal = Calendar.getInstance()
            cal.set(year, month, 1, 0, 0, 0)
            cal.set(Calendar.MILLISECOND, 0)
            val firstDow = cal.get(Calendar.DAY_OF_WEEK) // Sun=1..Sat=7
            val offset = (firstDow + 5) % 7 // convert to Monday-start
            cal.add(Calendar.DAY_OF_MONTH, -offset)

            val days = mutableListOf<Calendar>()
            repeat(42) {
                days.add(cal.clone() as Calendar)
                cal.add(Calendar.DAY_OF_MONTH, 1)
            }
            return days
        }
    }
}
