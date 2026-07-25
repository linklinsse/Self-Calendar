package app.selfcalendar.app.widget

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.app.PendingIntent
import android.widget.RemoteViews
import app.selfcalendar.app.R
import org.json.JSONArray
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class MonthWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, mgr: AppWidgetManager, ids: IntArray) {
        for (id in ids) updateWidget(context, mgr, id)
    }

    companion object {
        private val ISO = SimpleDateFormat("yyyy-MM-dd", Locale.US)

        fun updateWidget(context: Context, mgr: AppWidgetManager, widgetId: Int) {
            val pkg = context.packageName
            val root = RemoteViews(pkg, R.layout.month_widget)

            val prefs = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val eventsJson = prefs.getString("events", "[]") ?: "[]"
            val eventsByDate = parseEvents(eventsJson)

            val today = Calendar.getInstance()
            val monthTitleFmt = SimpleDateFormat("MMMM yyyy", Locale.getDefault())
            root.setTextViewText(R.id.month_title, monthTitleFmt.format(today.time))

            root.removeAllViews(R.id.days_container)

            val grid = buildMonthGrid(today.get(Calendar.YEAR), today.get(Calendar.MONTH))
            val currentMonth = today.get(Calendar.MONTH)

            for (week in 0 until 6) {
                val rowView = RemoteViews(pkg, R.layout.month_widget_row)
                for (col in 0 until 7) {
                    val day = grid[week * 7 + col]
                    val cell = buildCell(context, pkg, day, currentMonth, eventsByDate, widgetId * 100 + week * 7 + col)
                    rowView.addView(R.id.week_row, cell)
                }
                root.addView(R.id.days_container, rowView)
            }

            mgr.updateAppWidget(widgetId, root)
        }

        private fun buildCell(
            context: Context,
            pkg: String,
            day: Calendar,
            currentMonth: Int,
            eventsByDate: Map<String, List<String>>,
            requestCode: Int
        ): RemoteViews {
            val cell = RemoteViews(pkg, R.layout.month_widget_cell)
            val dateStr = ISO.format(day.time)
            val isToday = isSameDay(day, Calendar.getInstance())
            val isOutside = day.get(Calendar.MONTH) != currentMonth

            cell.setTextViewText(R.id.day_number, day.get(Calendar.DAY_OF_MONTH).toString())

            if (isToday) {
                cell.setInt(R.id.day_number, "setBackgroundResource", R.drawable.today_circle)
                cell.setTextColor(R.id.day_number, Color.parseColor("#1A0812"))
            } else {
                cell.setInt(R.id.day_number, "setBackgroundResource", 0)
                val textColor = if (isOutside) Color.parseColor("#9A8A90") else Color.parseColor("#1A0812")
                cell.setTextColor(R.id.day_number, textColor)
            }

            cell.removeAllViews(R.id.dots_container)
            val colors = eventsByDate[dateStr].orEmpty().take(4)
            for (colorHex in colors) {
                val dot = RemoteViews(pkg, R.layout.month_widget_dot)
                try {
                    dot.setInt(R.id.dot_image, "setColorFilter", Color.parseColor(colorHex))
                } catch (e: Exception) {
                    dot.setInt(R.id.dot_image, "setColorFilter", Color.GRAY)
                }
                cell.addView(R.id.dots_container, dot)
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

        private fun parseEvents(json: String): Map<String, List<String>> {
            val map = HashMap<String, MutableList<String>>()
            try {
                val arr = JSONArray(json)
                for (i in 0 until arr.length()) {
                    val obj = arr.getJSONObject(i)
                    val date = obj.getString("date")
                    val color = obj.optString("color", "#F4B8C8")
                    map.getOrPut(date) { mutableListOf() }.add(color)
                }
            } catch (e: Exception) { }
            return map
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
