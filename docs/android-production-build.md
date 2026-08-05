# Android production build

How to produce a release-signed APK (or AAB) of Self Calendar, by hand.

CI can do this too — see `ci/README.md` — but it needs the keystore as a
secret, and you have to create the keystore locally first regardless. This
document is that process.

---

## Prerequisites

- **JDK 21.** `app/android/app/build.gradle` sets `sourceCompatibility` and
  `jvmTarget` to 21; a different JDK will fail or produce surprising
  bytecode.
- **Android SDK.** Android Studio installs it; otherwise the command-line
  tools plus platform 34+ and build-tools.
- **Node 22** and the app's dependencies (`cd app && npm ci`).

```bash
java -version     # expect 21
echo $ANDROID_HOME
```

---

## Step 1 — Create a signing keystore (once, ever)

```bash
keytool -genkeypair -v \
  -keystore selfcalendar-release.keystore \
  -alias selfcalendar \
  -keyalg RSA -keysize 4096 -validity 10000 \
  -storetype PKCS12
```

You will be asked for a password and some identity fields. The identity
fields are not verified by anything and are not shown to users; the password
matters.

> **Back this file up somewhere you will still have in five years, and store
> the password separately.**
>
> Android identifies an app by its signing key. If you lose the keystore you
> cannot ship an update to anyone who already installed the app — not through
> Play, not through a direct APK. They would have to uninstall and lose their
> local data. There is no recovery process, no support ticket, nothing. This
> is the single most unrecoverable mistake available in Android development.

`selfcalendar-release.keystore` must never be committed. Check it is ignored:

```bash
git check-ignore -v app/android/selfcalendar-release.keystore
```

If that prints nothing, add it to `.gitignore` before going further.

---

## Step 2 — Build the web assets and sync them

The Android app is a WebView wrapper. Skipping this ships whatever was last
synced — usually nothing, which launches to a blank screen.

```bash
cd app
npm ci
npm run build          # -> app/build
npx cap sync android   # copies build/ into android/app/src/main/assets
```

**Check the backend address before building.** The APK bakes in whatever
`VITE_API_BASE_URL` was set at build time as its default. Users can override
it from the login screen (see `app/README.md`), but the default is what a
fresh install talks to:

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

---

## Step 3 — Build a signed APK

`app/android/app/build.gradle` deliberately has **no `signingConfig`** — a
keystore path in a build file is a mistake waiting to be committed. Pass the
signing details on the command line instead:

```bash
cd app/android

./gradlew assembleRelease \
  -PscVersionName="1.0.0" \
  -PscVersionCode=1 \
  -Pandroid.injected.signing.store.file="$HOME/keys/selfcalendar-release.keystore" \
  -Pandroid.injected.signing.store.password="$KEYSTORE_PASSWORD" \
  -Pandroid.injected.signing.key.alias="selfcalendar" \
  -Pandroid.injected.signing.key.password="$KEY_PASSWORD"
```

Output: `app/android/app/build/outputs/apk/release/app-release.apk`

Read the passwords from the environment rather than typing them inline —
otherwise they land in your shell history:

```bash
read -rs KEYSTORE_PASSWORD; export KEYSTORE_PASSWORD
read -rs KEY_PASSWORD;      export KEY_PASSWORD
```

### About `versionCode`

`versionCode` must **strictly increase** with every build you distribute.
Android compares that integer, not `versionName`, to decide whether something
is an upgrade. A build with an equal or lower code will not install over an
existing one.

Do not derive it from the semantic version by concatenating digits — `1.10.0`
and `1.1.0` collide under most obvious schemes, and once a wrong code is
published you cannot go back. CI uses the workflow run number for this
reason. By hand, keep a counter and increment it.

---

## Step 4 — Verify the APK before shipping it

```bash
cd app/android/app/build/outputs/apk/release

# Signed, and with what?
$ANDROID_HOME/build-tools/34.0.0/apksigner verify --verbose --print-certs app-release.apk

# Version, permissions and the launchable activity
$ANDROID_HOME/build-tools/34.0.0/aapt2 dump badging app-release.apk | head -20
```

Check that:

- it reports **v2** (and ideally v3) signature schemes as verified,
- the certificate fingerprint matches the one you expect — compare against
  previous releases, since a changed fingerprint means a changed key and an
  app nobody can upgrade,
- `versionCode` and `versionName` are what you intended,
- permissions are only `INTERNET` (and whatever you have deliberately added).
  Self Calendar does **not** request `READ_CALENDAR`/`WRITE_CALENDAR` — the
  device-calendar export goes through an intent instead. If those appear,
  something has changed that should not have.

Then install it on a real device and check it actually works:

```bash
adb install -r app-release.apk
```

**Test these specifically**, because they are the parts least covered by
automated tests:

- Sign in, and change the server address from the login screen.
- Add the home-screen widget; confirm it shows today's events.
- Leave the widget for more than 24 hours and confirm it still updates. That
  is the access-token expiry path, and its refresh-and-retry logic has never
  been verified on hardware.
- Open an event and use the device-calendar export. Confirm the system
  calendar editor opens prefilled, and that the link in the description
  reopens the event in Self Calendar.
- Tap that link with the app fully closed, not just backgrounded — that is a
  different code path (`App.getLaunchUrl()`).

---

## Building an AAB for Google Play

Play requires an Android App Bundle, not an APK:

```bash
cd app/android
./gradlew bundleRelease \
  -PscVersionName="1.0.0" \
  -PscVersionCode=1 \
  -Pandroid.injected.signing.store.file="$HOME/keys/selfcalendar-release.keystore" \
  -Pandroid.injected.signing.store.password="$KEYSTORE_PASSWORD" \
  -Pandroid.injected.signing.key.alias="selfcalendar" \
  -Pandroid.injected.signing.key.password="$KEY_PASSWORD"
```

Output: `app/android/app/build/outputs/bundle/release/app-release.aab`

If you enrol in Play App Signing, Google holds the *app* signing key and your
keystore becomes the *upload* key — which is recoverable if lost. That is a
meaningful safety improvement over self-signing and worth considering before
your first upload, because you cannot switch afterwards without support
involvement.

---

## Troubleshooting

**Blank screen on launch.** `npx cap sync android` was not run after
`npm run build`, so the WebView has no assets.

**"App not installed" on a device that already has it.** The signing key
differs from the installed copy — a debug build over a release build, or a
different keystore. Uninstall first; the user's local data goes with it.

**`INSTALL_FAILED_VERSION_DOWNGRADE`.** `versionCode` is not higher than the
installed one.

**Widget stays empty.** Confirm the app itself can reach the API. The widget
uses the same stored token and base URL, so if the app works and the widget
does not, check logcat:

```bash
adb logcat -s WidgetDataFetcher
```

**Release build succeeds but the APK will not install, and `apksigner`
reports it as unsigned.** The `-Pandroid.injected.signing.*` properties were
not picked up — usually a typo in a property name, which Gradle ignores
silently rather than failing.
