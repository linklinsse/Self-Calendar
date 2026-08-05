#!/bin/sh
# Runs as root (the container's default user — see Dockerfile) so it can
# fix ownership of the bind-mounted ./db volume before dropping to the
# unprivileged `nonroot` user to actually run the app.
#
# Why this is needed: `chown nonroot /work/db` at *build* time (see
# Dockerfile) only takes effect when nothing is mounted over it. Once
# docker-compose.yml bind-mounts the host's ./db over /work/db, its
# contents take on the *host* directory's ownership instead — which is
# whatever user created it there, essentially never uid 999. Without this,
# `nonroot` can't write prod.db and the API fails to start
# ("sqlite3.OperationalError: unable to open database file").
set -e

# The obvious/expected case: DB_URL points inside the ./db volume mount.
chown -R nonroot:nonroot /work/db

# Defensive fallback: DB_URL doesn't have to point inside /work/db — it's
# just whatever conf/.env says, and there are two different .env.template
# files in this repo (root vs api/) with two different defaults
# (./db/prod.db vs ./dev.db). If the wrong one gets copied to conf/.env,
# DB_URL resolves outside the volume mount entirely (e.g. /work/dev.db),
# which the chown above doesn't reach, and /work itself is root-owned
# (built into the image) — so also resolve DB_URL the same way the app
# itself will and chown *that* directory too, in case it's somewhere else
# under /work. Best-effort: settings resolution failing here shouldn't
# block startup, since the real error (if any) will surface clearly from
# the app itself right after this.
DB_DIR="$(uv run python -c "
import os
from app.common.config import settings
url = settings.DB_URL
path = url.removeprefix('sqlite:///') if url.startswith('sqlite:///') else None
print(os.path.dirname(path) if path else '', end='')
" 2>/dev/null || true)"
if [ -n "$DB_DIR" ]; then
    mkdir -p "$DB_DIR"
    chown -R nonroot:nonroot "$DB_DIR"
fi

# setpriv changes uid/gid but not $HOME — without this, uv still looks for
# its cache under /root (from the image's build-time root user) and fails
# with a permission error since nonroot can't write there.
export HOME=/home/nonroot

exec setpriv --reuid=nonroot --regid=nonroot --init-groups "$@"
