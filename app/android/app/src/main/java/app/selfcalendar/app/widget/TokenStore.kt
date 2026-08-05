package app.selfcalendar.app.widget

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Stores the widget's auth token in its own encrypted-at-rest prefs file,
 * separate from "widget_data" (theme/events/api_base_url — not sensitive).
 * A bearer token is a bigger target than the rest of that file's contents:
 * plain SharedPreferences is only protected by app-sandboxing on a
 * non-rooted device, and (unlike the rest of "widget_data") this file is
 * also excluded from Android auto-backup — see the backup rules XMLs.
 */
object TokenStore {
    private const val FILE_NAME = "widget_secure_data"
    private const val KEY_TOKEN = "auth_token"
    private const val KEY_REFRESH_TOKEN = "refresh_token"

    private fun prefs(context: Context): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        return EncryptedSharedPreferences.create(
            context,
            FILE_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    fun save(context: Context, token: String) {
        prefs(context).edit().putString(KEY_TOKEN, token).apply()
    }

    fun load(context: Context): String? = prefs(context).getString(KEY_TOKEN, null)

    /**
     * Replace only the access token, leaving the refresh token in place.
     *
     * Used after a successful refresh: the refresh token is still valid and
     * still needed, so a plain save() (which the app calls on login/logout
     * with both) must not be reused here.
     */
    fun saveAccessToken(context: Context, token: String) {
        prefs(context).edit().putString(KEY_TOKEN, token).apply()
    }

    /**
     * The long-lived token used to mint new access tokens.
     *
     * The widget needs this because it keeps rendering for weeks without the
     * user necessarily opening the app, while an access token lasts a day —
     * without it the widget silently froze on stale data once the token
     * expired, with no way to recover short of signing in again.
     */
    fun saveRefreshToken(context: Context, refreshToken: String) {
        prefs(context).edit().putString(KEY_REFRESH_TOKEN, refreshToken).apply()
    }

    fun loadRefreshToken(context: Context): String? =
        prefs(context).getString(KEY_REFRESH_TOKEN, null)

    fun clear(context: Context) {
        prefs(context).edit().remove(KEY_TOKEN).remove(KEY_REFRESH_TOKEN).apply()
    }
}
