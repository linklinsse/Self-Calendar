package app.selfcalendar.app.widget

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.net.Uri
import android.os.Build
import android.app.PendingIntent
import android.util.TypedValue
import android.view.View
import android.widget.RemoteViews
import androidx.annotation.RequiresApi
import app.selfcalendar.app.R
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.ConcurrentHashMap

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
    // Stable row index for a multi-day event, shared across every day it
    // spans (see WidgetDataFetcher.buildEventsByDate). Null for a single-day
    // event, which instead fills whatever row is free after the reserved
    // slots. Without this, each day picked the multi-day event's row
    // independently (by whatever else happened to share that day), so the
    // same event could land on row 1 one day and row 2 the next — it never
    // read as one continuous event when scanning across its span.
    val slot: Int?,
    // True on the occurrence's actual first/last day (only meaningful when
    // slot != null). Drives buildCell's banner rendering — title text and
    // rounded corners only appear on these days, so a multi-day event reads
    // as one continuous bar across the week instead of a pill repeated on
    // every day it touches, mirroring MonthView.svelte's banner-layer.
    val spanStart: Boolean = false,
    val spanEnd: Boolean = false,
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
        for (id in appWidgetIds) {
            editor.remove(PREF_OFFSET_PREFIX + id)
            navGeneration.remove(id)
        }
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
        // stale for this month until the fetch below lands).
        updateWidget(context, mgr, widgetId)

        // Fetch starts immediately — no debounce — so the new month's real
        // events show up as fast as the network allows rather than waiting
        // out an artificial delay first. A burst of rapid taps still can't
        // leave the widget on the wrong month's data: each tap bumps this
        // widget's generation counter, and a fetch only gets to write its
        // result if that counter hasn't moved on since — a slower fetch for
        // a month the user has already navigated away from just discards
        // itself instead of landing last and overwriting the correct one.
        val generation = navGeneration.merge(widgetId, 1) { old, delta1 -> old + delta1 } ?: 1
        val pending = goAsync()
        Thread {
            try {
                refreshWidgetDataAndRender(context, mgr, widgetId, generation)
            } finally {
                pending.finish()
            }
        }.start()
    }

    companion object {
        private const val ACTION_PREV_MONTH = "app.selfcalendar.app.widget.ACTION_PREV_MONTH"
        private const val ACTION_NEXT_MONTH = "app.selfcalendar.app.widget.ACTION_NEXT_MONTH"
        private const val PREF_OFFSET_PREFIX = "month_offset_"

        // Per-widget nav counter — see onReceive's comment above.
        private val navGeneration = ConcurrentHashMap<Int, Int>()

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
        private val EVENT_BG_IDS = listOf(R.id.event_bg_1, R.id.event_bg_2, R.id.event_bg_3)

        // Arbitrary fixed resolution for the spanning-event pill bitmap —
        // like BG_BITMAP_SIZE/TODAY_CIRCLE_BITMAP_SIZE, ImageView (fitXY)
        // stretches it to the real row bounds, so only the aspect ratio
        // (which sets how round the corners look) matters here.
        private const val PILL_BITMAP_W = 200
        private const val PILL_BITMAP_H = 40

        // banner_overlay geometry (see month_widget_row.xml / addBannerSegment).
        // BANNER_TOP_OFFSET_DP clears the day-number row: cell_root's 2dp top
        // padding + the 18dp day-number circle + the 1dp margin above the
        // event-row stack (all from month_widget_cell.xml) = 21dp before the
        // first event row starts. OUTER_PADDING_DP matches month_widget.xml's
        // own android:padding="10dp", which is what makes days_container
        // narrower than the widget's own reported width.
        private const val BANNER_H_DP = 13f
        private const val BANNER_GAP_DP = 2f
        private const val BANNER_TOP_OFFSET_DP = 21f
        private const val BANNER_SEGMENT_INSET_DP = 3f
        private const val OUTER_PADDING_DP = 10f

        private val ISO = SimpleDateFormat("yyyy-MM-dd", Locale.US)

        fun updateWidget(context: Context, mgr: AppWidgetManager, widgetId: Int) {
            val pkg = context.packageName
            val root = RemoteViews(pkg, R.layout.month_widget)

            val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val eventsJson = prefs.getString("events", "[]") ?: "[]"
            val eventsByDate = parseEvents(eventsJson)
            val theme = parseTheme(prefs.getString("theme", null))
            val monthOffset = prefs.getInt(PREF_OFFSET_PREFIX + widgetId, 0)
            val locale = parseLocale(prefs.getString("locale", null))
            // 0=Sunday..6=Saturday, matching config.js's FIRST_DAY_OF_WEEK —
            // defaults to Monday, same as config.js's own default, for the
            // brief window before the app has ever synced this.
            val firstDayOfWeek = prefs.getInt("first_day_of_week", 1)

            val anchor = Calendar.getInstance()
            anchor.add(Calendar.MONTH, monthOffset)

            val monthTitleFmt = SimpleDateFormat("MMMM yyyy", Locale.getDefault())
            root.setTextViewText(R.id.month_title, monthTitleFmt.format(anchor.time))

            root.setImageViewBitmap(R.id.widget_bg_image, roundedRectBitmap(BG_BITMAP_SIZE, theme.bg))
            root.setTextColor(R.id.month_title, theme.text)
            root.setTextColor(R.id.btn_prev_month, theme.text)
            root.setTextColor(R.id.btn_next_month, theme.text)
            root.setTextColor(R.id.btn_add_event, theme.text)
            val dowLabels = weekdayLabels(locale, firstDayOfWeek)
            for (i in DOW_IDS.indices) {
                root.setTextViewText(DOW_IDS[i], dowLabels[i])
                root.setTextColor(DOW_IDS[i], theme.textMuted)
            }

            root.setOnClickPendingIntent(R.id.btn_prev_month, navPendingIntent(context, widgetId, ACTION_PREV_MONTH))
            root.setOnClickPendingIntent(R.id.btn_next_month, navPendingIntent(context, widgetId, ACTION_NEXT_MONTH))
            // requestCode 99 is outside buildCell's own per-widget requestCode
            // range (widgetId * 100 + week*7+col, max 41), so this can't
            // collide with a day cell's own PendingIntent.
            root.setOnClickPendingIntent(
                R.id.btn_add_event,
                deepLinkPendingIntent(context, widgetId * 100 + 99, "selfcalendar://new")
            )

            root.removeAllViews(R.id.days_container)

            val grid = buildMonthGrid(anchor.get(Calendar.YEAR), anchor.get(Calendar.MONTH), firstDayOfWeek)
            val currentMonth = anchor.get(Calendar.MONTH)

            // Full-width banner titles need the widget's actual on-screen
            // width (setViewLayoutWidth/setViewLayoutMargin, both API 31+)
            // — below that, or before the host has reported a usable width,
            // banner_overlay is left empty and buildCell's own per-cell
            // (single-column, still-connected-bar) title stands in instead.
            val cellWidthDp = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
                computeCellWidthDp(mgr, widgetId) else 0f
            val useBannerOverlay = cellWidthDp > 0f

            for (week in 0 until 6) {
                val rowView = RemoteViews(pkg, R.layout.month_widget_row)
                val days = (0 until 7).map { grid[week * 7 + it] }
                for (col in 0 until 7) {
                    val day = days[col]
                    val cell = buildCell(
                        context, pkg, day, currentMonth, eventsByDate, theme,
                        widgetId * 100 + week * 7 + col, col,
                        suppressSpanningTitle = useBannerOverlay,
                    )
                    rowView.addView(R.id.week_row, cell)
                }
                if (useBannerOverlay && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    for (seg in buildBannerSegments(days, eventsByDate)) {
                        addBannerSegment(pkg, rowView, seg, cellWidthDp)
                    }
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
         *
         * @param expectedGeneration when set (nav-triggered refreshes — see
         *   onReceive), the fetched result is discarded instead of written
         *   if this widget has since navigated to a different month —
         *   otherwise a slow fetch for a month the user already left could
         *   land after a faster one for where they actually are and
         *   overwrite it with the wrong month's events. Left null for the
         *   periodic/onUpdate refresh, which isn't racing anything.
         */
        fun refreshWidgetDataAndRender(
            context: Context,
            mgr: AppWidgetManager,
            widgetId: Int,
            expectedGeneration: Int? = null,
        ) {
            val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val monthOffset = prefs.getInt(PREF_OFFSET_PREFIX + widgetId, 0)
            val firstDayOfWeek = prefs.getInt("first_day_of_week", 1)
            val anchor = Calendar.getInstance()
            anchor.add(Calendar.MONTH, monthOffset)
            val grid = buildMonthGrid(anchor.get(Calendar.YEAR), anchor.get(Calendar.MONTH), firstDayOfWeek)

            val fresh = WidgetDataFetcher.fetchWidgetData(context, grid.first(), grid.last()) ?: return
            if (expectedGeneration != null && navGeneration[widgetId] != expectedGeneration) return
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
                    if (ev.slot != null) obj.put("slot", ev.slot) else obj.put("slot", JSONObject.NULL)
                    obj.put("spanStart", ev.spanStart)
                    obj.put("spanEnd", ev.spanEnd)
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
            requestCode: Int,
            col: Int,
            suppressSpanningTitle: Boolean = false,
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

            // Multi-day events carry a `slot` — the same row index on every
            // day they span (see WidgetDataFetcher.buildEventsByDate) — so
            // they go in that fixed row first. Rows spanning events reserve
            // but don't occupy on *this* particular day stay reserved (drawn
            // empty, not collapsed) so a later row doesn't shift up and make
            // a still-ongoing event look like it moved. Single-day events
            // then fill whatever rows are left, in their existing order.
            val rows = arrayOfNulls<WidgetEvent>(MAX_SHOWN_PER_DAY)
            var reservedRows = 0
            for (ev in dayEvents) {
                val slot = ev.slot ?: continue
                if (slot < MAX_SHOWN_PER_DAY) rows[slot] = ev
                reservedRows = maxOf(reservedRows, slot + 1)
            }
            var nextFree = reservedRows
            for (ev in dayEvents) {
                if (ev.slot != null) continue
                if (nextFree >= MAX_SHOWN_PER_DAY) break
                rows[nextFree] = ev
                nextFree++
            }

            // Whether *any* row's banner needs to bleed through cell_root's
            // own 1dp start/end padding (see below) — set while walking the
            // rows, applied once after the loop.
            var bleedStart = false
            var bleedEnd = false

            for (i in EVENT_ROW_IDS.indices) {
                val ev = rows[i]
                if (ev != null) {
                    cell.setViewVisibility(EVENT_ROW_IDS[i], View.VISIBLE)

                    val evColor = try { Color.parseColor(ev.color) } catch (e: Exception) { Color.GRAY }
                    if (ev.slot != null || ev.allDay) {
                        // Multi-day (spanning) event, OR a plain single-day
                        // all-day event — both get the same full-bleed,
                        // rounded-corner banner treatment (mirrors
                        // MonthView.svelte's banner-layer) instead of the
                        // smaller inset pill timed events use, so the label
                        // gets the full width of the cell to work with. A
                        // single-day all-day event has no neighbor to
                        // connect to, so it's always rounded on both ends;
                        // a spanning event's *visual* start/end — its true
                        // first/last day, OR this cell's grid row wrapping
                        // (col 0 / col 6) — decides rounding + title, so a
                        // banner that spans a week boundary restarts
                        // (rounded + labeled again) on the next row instead
                        // of only ever showing once, mirroring how Google
                        // Calendar re-labels a multi-day event at the start
                        // of each week it touches.
                        val visualStart = if (ev.slot != null) (ev.spanStart || col == 0) else true
                        val visualEnd   = if (ev.slot != null) (ev.spanEnd   || col == 6) else true
                        cell.setInt(EVENT_ROW_IDS[i], "setBackgroundColor", Color.TRANSPARENT)
                        cell.setViewVisibility(EVENT_BG_IDS[i], View.VISIBLE)
                        cell.setImageViewBitmap(EVENT_BG_IDS[i], pillBitmap(evColor, visualStart, visualEnd))
                        cell.setViewVisibility(EVENT_ACCENT_IDS[i], View.GONE)
                        // One label per banner, on its true (visual) start
                        // day only — not repeated on every day it spans.
                        // The background still bleeds the full width (see
                        // the padding logic below); only the title is
                        // single-shot, matching a normal multi-day event
                        // banner instead of the label re-reading itself on
                        // every cell.
                        //
                        // When banner_overlay is rendering titles instead
                        // (suppressSpanningTitle — see updateWidget), this
                        // per-cell label is left blank on a *spanning*
                        // event's cells: it's confined to one day cell's
                        // width and would otherwise show a redundant,
                        // more-truncated copy right next to the full-width
                        // one. A single-day all-day event (ev.slot == null)
                        // has no banner_overlay counterpart at all — it must
                        // always show its own label here, or it'd render
                        // with no text.
                        val labelSuppressed = suppressSpanningTitle && ev.slot != null
                        cell.setTextViewText(
                            EVENT_TITLE_IDS[i],
                            if (visualStart && !labelSuppressed) ev.title else ""
                        )
                        cell.setTextColor(EVENT_TITLE_IDS[i], TODAY_TEXT_COLOR)
                        // Close the row's own left/right padding on whichever
                        // side connects to a neighboring day of the same
                        // event, so consecutive cells merge into one bar
                        // instead of reading as separated pills (the ~4dp of
                        // padding baked into month_widget_cell.xml otherwise
                        // shows as a gap between every day).
                        val padV = dpToPx(context, 1)
                        val padH = dpToPx(context, 2)
                        cell.setViewPadding(
                            EVENT_ROW_IDS[i],
                            if (visualStart) padH else 0, padV,
                            if (visualEnd) padH else 0, padV
                        )
                        if (!visualStart) bleedStart = true
                        if (!visualEnd) bleedEnd = true
                    } else {
                        // Timed event — mirrors .ev-pill: ~26% tinted fill
                        // (CSS `color42`), color text, colored left accent bar.
                        cell.setViewVisibility(EVENT_BG_IDS[i], View.GONE)
                        cell.setTextViewText(EVENT_TITLE_IDS[i], ev.title)
                        cell.setInt(EVENT_ROW_IDS[i], "setBackgroundColor", withAlpha(evColor, 0x42))
                        cell.setViewVisibility(EVENT_ACCENT_IDS[i], View.VISIBLE)
                        cell.setInt(EVENT_ACCENT_IDS[i], "setColorFilter", evColor)
                        cell.setTextColor(EVENT_TITLE_IDS[i], evColor)
                    }
                } else if (i < reservedRows) {
                    // Reserved for a spanning event not present today —
                    // INVISIBLE (not GONE) keeps its row height so lower
                    // rows don't shift.
                    cell.setViewVisibility(EVENT_ROW_IDS[i], View.INVISIBLE)
                } else {
                    cell.setViewVisibility(EVENT_ROW_IDS[i], View.GONE)
                }
            }

            if (bleedStart || bleedEnd) {
                // cell_root's own 1dp start/end padding (month_widget_cell.xml)
                // is the last bit of gap left once a banner row's own padding
                // is already closed (above) — without also zeroing this, two
                // adjacent days of the same spanning event still show a hairline
                // seam between them. Only zeroed on the side(s) a banner
                // actually bleeds through; day_number's own fixed-size box is
                // unaffected since it isn't sized off this padding.
                cell.setViewPadding(
                    R.id.cell_root,
                    if (bleedStart) 0 else dpToPx(context, 1), dpToPx(context, 2),
                    if (bleedEnd) 0 else dpToPx(context, 1), 0
                )
            }

            val shownCount = rows.count { it != null }
            val remaining = dayEvents.size - shownCount
            if (remaining > 0) {
                cell.setViewVisibility(R.id.overflow_text, View.VISIBLE)
                cell.setTextViewText(R.id.overflow_text, "+$remaining")
                cell.setTextColor(R.id.overflow_text, theme.textMuted)
            } else {
                cell.setViewVisibility(R.id.overflow_text, View.GONE)
            }

            cell.setOnClickPendingIntent(
                R.id.cell_root,
                deepLinkPendingIntent(context, requestCode, "selfcalendar://day?date=$dateStr")
            )

            return cell
        }

        /** A PendingIntent that opens MainActivity on `uri` — the same deep links
         * src/routes/+layout.svelte's handleUrl() already handles for links tapped
         * outside the app (day/new/event). requestCode must be unique per distinct
         * click target sharing this app/activity, or FLAG_UPDATE_CURRENT would make
         * them collide into one PendingIntent. */
        private fun deepLinkPendingIntent(context: Context, requestCode: Int, uri: String): PendingIntent {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(uri), context, Class.forName("app.selfcalendar.app.MainActivity"))
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            return PendingIntent.getActivity(
                context, requestCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }

        /**
         * days_container is inset from the widget's own reported width by
         * month_widget.xml's 10dp padding on each side; days is 7 equal
         * columns within what's left. Returns 0f (meaning "don't render
         * banner_overlay this pass") until the widget host has reported a
         * usable width — the brief window right after a widget is placed,
         * before the system has measured it.
         */
        private fun computeCellWidthDp(mgr: AppWidgetManager, widgetId: Int): Float {
            val minWidthDp = try {
                mgr.getAppWidgetOptions(widgetId).getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, 0)
            } catch (e: Exception) {
                0
            }
            val contentWidthDp = minWidthDp - OUTER_PADDING_DP * 2
            return if (contentWidthDp > 0f) contentWidthDp / 7f else 0f
        }

        /** One multi-day event's title run within a single week's row — see buildBannerSegments. */
        private data class BannerSegment(
            val col: Int,   // 0-6, first column (day) this run covers in this row
            val span: Int,  // number of columns it covers, 1-7
            val slot: Int,  // vertical lane — shared with the per-cell reserved rows in buildCell
            val title: String,
        )

        /**
         * Turns one week's worth of already-bucketed WidgetEvents (the same
         * `eventsByDate` buildCell reads) into one BannerSegment per
         * contiguous run of days a spanning event actually covers *in this
         * row* — i.e. exactly what buildCell already treats as one visual
         * banner (visualStart..visualEnd, see there), just resolved once per
         * row instead of re-derived independently by every cell.
         *
         * Two different events can legitimately reuse the same slot number
         * within one row (assignSpanningSlots in WidgetDataFetcher reuses a
         * slot once its previous occupant has ended), so this walks the row
         * day by day and closes/reopens a run per slot rather than assuming
         * one run per slot.
         */
        private fun buildBannerSegments(
            days: List<Calendar>,
            eventsByDate: Map<String, List<WidgetEvent>>,
        ): List<BannerSegment> {
            data class Open(val startCol: Int, val title: String)

            val segments = mutableListOf<BannerSegment>()
            val open = HashMap<Int, Open>()

            for (col in 0..6) {
                val dateStr = ISO.format(days[col].time)
                val bySlot = eventsByDate[dateStr].orEmpty()
                    .filter { it.slot != null }
                    .associateBy { it.slot!! }

                // A slot with nothing scheduled today closes whatever run was
                // open for it — normally only reached via spanEnd below, this
                // is just a defensive close in case the data ever has a gap
                // mid-span.
                val absent = open.keys.filter { it !in bySlot }
                for (slot in absent) {
                    val o = open.remove(slot)!!
                    segments.add(BannerSegment(o.startCol, col - o.startCol, slot, o.title))
                }

                for ((slot, ev) in bySlot) {
                    if (slot !in open) open[slot] = Open(col, ev.title)
                    if (ev.spanEnd || col == 6) {
                        val o = open.remove(slot)!!
                        segments.add(BannerSegment(o.startCol, col - o.startCol + 1, slot, o.title))
                    }
                }
            }
            return segments
        }

        /**
         * Adds one banner title to `banner_overlay`, sized and positioned in
         * real dp via setViewLayoutWidth/setViewLayoutMargin (RemoteViews,
         * API 31+) so it spans its true run of days — see
         * month_widget_row.xml and month_widget_banner_segment.xml. Callers
         * must not invoke this below API 31.
         */
        @RequiresApi(Build.VERSION_CODES.S)
        private fun addBannerSegment(pkg: String, rowView: RemoteViews, seg: BannerSegment, cellWidthDp: Float) {
            val view = RemoteViews(pkg, R.layout.month_widget_banner_segment)
            view.setTextViewText(R.id.banner_title, seg.title)

            val widthDp = (cellWidthDp * seg.span - BANNER_SEGMENT_INSET_DP).coerceAtLeast(0f)
            val marginStartDp = cellWidthDp * seg.col + BANNER_SEGMENT_INSET_DP / 2f
            val marginTopDp = BANNER_TOP_OFFSET_DP + seg.slot * (BANNER_H_DP + BANNER_GAP_DP)

            view.setViewLayoutWidth(R.id.banner_title, widthDp, TypedValue.COMPLEX_UNIT_DIP)
            view.setViewLayoutHeight(R.id.banner_title, BANNER_H_DP, TypedValue.COMPLEX_UNIT_DIP)
            view.setViewLayoutMargin(R.id.banner_title, RemoteViews.MARGIN_START, marginStartDp, TypedValue.COMPLEX_UNIT_DIP)
            view.setViewLayoutMargin(R.id.banner_title, RemoteViews.MARGIN_TOP, marginTopDp, TypedValue.COMPLEX_UNIT_DIP)

            rowView.addView(R.id.banner_overlay, view)
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
                    // isNull() also covers a cache written before "slot"
                    // existed (missing key), which safely falls back to
                    // "not a spanning event" rather than crashing.
                    val slot = if (obj.isNull("slot")) null else obj.optInt("slot")
                    // optBoolean defaults to false for a cache written before
                    // these existed, which is the right fallback: treat every
                    // day of an old-cached spanning event as neither the true
                    // start nor end until the next fetch repopulates it.
                    val spanStart = obj.optBoolean("spanStart", false)
                    val spanEnd = obj.optBoolean("spanEnd", false)
                    map.getOrPut(date) { mutableListOf() }
                        .add(WidgetEvent(title, color, allDay, startMinutes, slot, spanStart, spanEnd))
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

        /**
         * A rectangle tinted `color`, rounded only on the corners a
         * spanning event's banner should show as rounded: the left corners
         * on its true start day, the right corners on its true end day,
         * square otherwise. That's what makes consecutive days of the same
         * multi-day event read as one continuous bar (see buildCell) rather
         * than a row of separately-rounded pills, without needing a single
         * View that actually spans multiple day cells — which RemoteViews
         * can't do reliably here (see the comment atop month_widget_cell.xml).
         */
        private fun pillBitmap(color: Int, roundStart: Boolean, roundEnd: Boolean): Bitmap {
            val bmp = Bitmap.createBitmap(PILL_BITMAP_W, PILL_BITMAP_H, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bmp)
            val paint = Paint(Paint.ANTI_ALIAS_FLAG)
            paint.color = color
            val r = PILL_BITMAP_H * 0.35f
            val sr = if (roundStart) r else 0f
            val er = if (roundEnd) r else 0f
            // Corner order: top-left, top-right, bottom-right, bottom-left —
            // each as an (x, y) radius pair.
            val radii = floatArrayOf(sr, sr, er, er, er, er, sr, sr)
            val path = Path()
            path.addRoundRect(RectF(0f, 0f, PILL_BITMAP_W.toFloat(), PILL_BITMAP_H.toFloat()), radii, Path.Direction.CW)
            canvas.drawPath(path, paint)
            return bmp
        }

        private fun dpToPx(context: Context, dp: Int): Int =
            (dp * context.resources.displayMetrics.density).toInt()

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

        /** @param firstDayOfWeek 0=Sunday..6=Saturday, matching config.js's FIRST_DAY_OF_WEEK. */
        private fun buildMonthGrid(year: Int, month: Int, firstDayOfWeek: Int): List<Calendar> {
            val cal = Calendar.getInstance()
            cal.set(year, month, 1, 0, 0, 0)
            cal.set(Calendar.MILLISECOND, 0)
            val firstDow = cal.get(Calendar.DAY_OF_WEEK) - 1 // Sun=1..Sat=7 -> Sun=0..Sat=6
            val offset = (firstDow - firstDayOfWeek + 7) % 7
            cal.add(Calendar.DAY_OF_MONTH, -offset)

            val days = mutableListOf<Calendar>()
            repeat(42) {
                days.add(cal.clone() as Calendar)
                cal.add(Calendar.DAY_OF_MONTH, 1)
            }
            return days
        }

        /** BCP-47 tag as sent by config.js's LOCALE (e.g. "fr-FR") -> Locale, falling
         * back to the device locale if nothing has synced yet or the tag is blank. */
        private fun parseLocale(tag: String?): Locale {
            if (tag.isNullOrBlank()) return Locale.getDefault()
            return Locale.forLanguageTag(tag)
        }

        /**
         * Weekday header labels in `locale`, ordered starting at
         * `firstDayOfWeek` (0=Sunday..6=Saturday) — the native equivalent of
         * utils.js's DOW_LETTERS, which is what MonthView.svelte's own
         * header uses. "EEEEE" is the narrow style (e.g. "M"/"T"/"W" in
         * en, "L"/"M"/"M" in fr), matching the { weekday: 'narrow' } Intl
         * option utils.js requests.
         *
         * 2023-01-01 is a fixed, known Sunday used purely as a labelling
         * anchor, read in UTC so the widget's own timezone can't shift it
         * onto a different weekday.
         */
        private fun weekdayLabels(locale: Locale, firstDayOfWeek: Int): List<String> {
            val fmt = SimpleDateFormat("EEEEE", locale)
            fmt.timeZone = TimeZone.getTimeZone("UTC")
            val cal = Calendar.getInstance(TimeZone.getTimeZone("UTC"))
            cal.set(2023, Calendar.JANUARY, 1, 0, 0, 0)
            cal.set(Calendar.MILLISECOND, 0)
            val sundayFirst = (0 until 7).map {
                val label = fmt.format(cal.time)
                cal.add(Calendar.DAY_OF_MONTH, 1)
                label
            }
            return (0 until 7).map { sundayFirst[(firstDayOfWeek + it) % 7] }
        }
    }
}
