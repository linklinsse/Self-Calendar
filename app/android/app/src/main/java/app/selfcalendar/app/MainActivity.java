package app.selfcalendar.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import app.selfcalendar.app.widget.WidgetBridgePlugin;
import app.selfcalendar.app.calendar.CalendarBridgePlugin;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(WidgetBridgePlugin.class);
        registerPlugin(CalendarBridgePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
