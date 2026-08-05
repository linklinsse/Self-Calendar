#!/bin/sh
# Inject runtime environment variables into the static build.
# This file is generated at container startup so env vars can change
# without rebuilding the image.
#
# Built with `jq -n --arg` rather than shell string interpolation: a `"` or
# newline in an operator-controlled env var (e.g. APP_NAME) would otherwise
# produce broken or injected JS in env-config.js.
env_json=$(jq -n \
  --arg apiBaseUrl "${API_BASE_URL}" \
  --arg theme "${THEME}" \
  --arg appName "${APP_NAME}" \
  --arg defaultView "${DEFAULT_VIEW}" \
  --arg firstDayOfWeek "${FIRST_DAY_OF_WEEK}" \
  --arg locale "${LOCALE}" \
  --arg hourFormat "${HOUR_FORMAT}" \
  '{
    API_BASE_URL: $apiBaseUrl,
    THEME: $theme,
    APP_NAME: $appName,
    DEFAULT_VIEW: $defaultView,
    FIRST_DAY_OF_WEEK: $firstDayOfWeek,
    LOCALE: $locale,
    HOUR_FORMAT: $hourFormat
  }')

echo "window.__ENV__ = ${env_json};" > /usr/share/nginx/html/env-config.js

exec nginx -g "daemon off;"
