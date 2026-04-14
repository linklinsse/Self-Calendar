"""
app/common/middleware/rate_limit_middleware.py
----------------------------------------------
IP-based rate limiter for sensitive routes.

How it works:
    - A per-IP failure counter is maintained in memory.
    - When the counter reaches RATE_LIMIT_MAX_FAILURES consecutive failures
      (any 4xx response) on a protected route, the IP is blocked for
      RATE_LIMIT_TIMEOUT_SECONDS seconds.
    - A successful response (2xx) resets the failure counter for that IP.
    - Blocked IPs receive HTTP 429 immediately, before the route handler runs.

Protected routes are defined in PROTECTED_ROUTES below as (method, path) pairs.
Add or remove entries there — no other file needs to change.

Configuration (via .env / environment):
    RATE_LIMIT_MAX_FAILURES    int  default 5    consecutive failures before block
    RATE_LIMIT_TIMEOUT_SECONDS int  default 180  seconds the block lasts

Note: The counter is in-process memory. It resets on server restart and is not
shared across multiple workers. For multi-worker production deployments, replace
`_store` with a Redis-backed store.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.common.config import settings

# ── Protected routes ──────────────────────────────────────────────────────────
# Only requests whose (METHOD, path) appear here contribute to the failure
# counter. All other routes pass through without any rate-limit tracking.

PROTECTED_ROUTES: set[tuple[str, str]] = {
    ("POST", "/auth/login"),
    ("POST", "/auth/register"),
    ("POST", "/user_calendar/"),
}

# ── In-memory store ───────────────────────────────────────────────────────────
# { ip: { "failures": int, "locked_until": float | None } }
# CPython's GIL protects individual dict operations, which is sufficient here.
# Replace with a Redis client for multi-worker / distributed setups.

_store: dict[str, dict] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Block IPs that repeatedly fail on sensitive routes."""

    async def dispatch(self, request: Request, call_next):
        route_key = (request.method, request.url.path)

        # Fast path: not a protected route — pass straight through.
        if route_key not in PROTECTED_ROUTES:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        # ── Check if this IP is currently blocked ─────────────────────────
        record = _store.get(ip)
        if record and record["locked_until"] and now < record["locked_until"]:
            remaining = int(record["locked_until"] - now)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "error_code": "RATE_LIMITED",
                        "message": (
                            f"Too many failed attempts. "
                            f"Try again in {remaining} seconds."
                        ),
                    }
                },
            )

        # ── Forward the request ───────────────────────────────────────────
        response = await call_next(request)

        # ── Update the failure counter based on the response ──────────────
        if response.status_code >= 400:
            rec = _store.setdefault(ip, {"failures": 0, "locked_until": None})
            rec["failures"] += 1

            if rec["failures"] >= settings.RATE_LIMIT_MAX_FAILURES:
                rec["locked_until"] = time.time() + settings.RATE_LIMIT_TIMEOUT_SECONDS
                rec["failures"] = 0  # reset so counter is clean after the block expires
                print(
                    f"[RateLimit] IP {ip} blocked for "
                    f"{settings.RATE_LIMIT_TIMEOUT_SECONDS}s after "
                    f"{settings.RATE_LIMIT_MAX_FAILURES} consecutive failures "
                    f"on {request.method} {request.url.path}"
                )
        else:
            # Successful response — clear the slate for this IP.
            _store.pop(ip, None)

        return response
