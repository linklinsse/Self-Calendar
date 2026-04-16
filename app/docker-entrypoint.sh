#!/bin/sh
# Inject runtime environment variables into the static build.
# This file is generated at container startup so env vars can change
# without rebuilding the image.
cat <<EOF > /usr/share/nginx/html/env-config.js
window.__ENV__ = {
  API_BASE_URL:     "${API_BASE_URL}",
  MOCK_MODE:        "${MOCK_MODE}",
  THEME:            "${THEME}",
  APP_NAME:         "${APP_NAME}",
  DEFAULT_VIEW:     "${DEFAULT_VIEW}",
  FIRST_DAY_OF_WEEK:"${FIRST_DAY_OF_WEEK}",
  LOCALE:           "${LOCALE}"
};
EOF

exec nginx -g "daemon off;"
