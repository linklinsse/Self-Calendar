FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY ./app /work/app
COPY ./migrations /work/migrations
COPY alembic.ini /work/
COPY uv.lock /work/
COPY pyproject.toml /work/

WORKDIR /work

# Disable development dependencies
ENV UV_NO_DEV=1
# Tells the app it is running in a container, so it can refuse to start on a
# database path that isn't on the mounted volume and would be destroyed by
# the next `docker compose down`. See _require_persistent_db in app/app.py.
ENV SELFCALENDAR_IN_CONTAINER=1

RUN uv sync --locked

RUN mkdir -p /work/db && chown -R nonroot:nonroot /work/db

# The container starts as root (default — no USER directive) so the
# entrypoint can fix up the bind-mounted ./db volume's ownership before
# dropping to `nonroot` to actually run the app — see docker-entrypoint.sh
# for why this is necessary and can't just be a build-time chown + USER.
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# autoheal (docker-compose.yml) restarts containers Docker reports as
# unhealthy — without a HEALTHCHECK, "unhealthy" never fires and it's a
# no-op. No curl/wget in this base image, so use python3 directly.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8082/docs', timeout=2)"]

CMD ["uv", "run", "fastapi", "run", "app/app.py", "--port", "8082"]