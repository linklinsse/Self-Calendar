"""
app/common/middleware/rate_limit_middleware.py
----------------------------------------------
IP-based rate limiter for sensitive routes.

How it works:
    - Each failed request (any 4xx/5xx response) on a protected route records
      a timestamp for the client IP.
    - When an IP accumulates RATE_LIMIT_MAX_FAILURES failures within the last
      RATE_LIMIT_WINDOW_SECONDS, it is blocked for RATE_LIMIT_TIMEOUT_SECONDS.
    - Blocked IPs receive HTTP 429 immediately, before the route handler runs.
    - A successful response does NOT clear the failures. It used to, and that
      made the limiter trivially bypassable: an attacker with any account of
      their own (or open registration) could log in successfully every few
      guesses to reset the counter, and brute-force another user's password
      from one IP at full speed. Failures now simply age out of the window.

Protected routes are defined in PROTECTED_ROUTES below as (method, path) pairs.
Add or remove entries there — no other file needs to change.

Configuration (via .env / environment):
    RATE_LIMIT_MAX_FAILURES    int  default 5    failures in the window before block
    RATE_LIMIT_WINDOW_SECONDS  int  default 900  how far back failures are counted
    RATE_LIMIT_TIMEOUT_SECONDS int  default 180  seconds the block lasts

Note: The counter is in-process memory. It resets on server restart and is not
shared across multiple workers. For multi-worker production deployments, replace
`_store` with a Redis-backed store.

Note: the key is the TCP peer address. Behind a reverse proxy every client
shares the proxy's address unless uvicorn is told to trust its
X-Forwarded-For (`--forwarded-allow-ips`), so one client's failures would
then block everyone.
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
    # Checks the caller's current password: without a limit, someone holding
    # a stolen (or borrowed-device) access token could guess it at full speed
    # and walk away with a password that is likely reused elsewhere.
    ("PATCH", "/user/password"),
}

# ── In-memory store ───────────────────────────────────────────────────────────
# { ip: { "failures": list[float], "locked_until": float | None,
#         "last_update": float } }
# `failures` holds the timestamps of recent failures, oldest first. It never
# grows past RATE_LIMIT_MAX_FAILURES: reaching that locks the IP and clears it.
# CPython's GIL protects individual dict operations, which is sufficient here.
# Replace with a Redis client for multi-worker / distributed setups.

_store: dict[str, dict] = {}

# An IP that never returns after tripping the limiter (or that trickles in a
# few failures below the threshold and never comes back) would otherwise
# stay in `_store` forever. Sweep out anything untouched for a while,
# checked opportunistically rather than via a background task/thread.
_SWEEP_INTERVAL_SECONDS = 300
_STALE_AFTER_SECONDS = 3600
_last_sweep = 0.0


def _stale_after() -> float:
    """An entry may only be dropped once nothing in it can matter any more:
    neither a failure still inside the window nor a lock still running."""
    return max(
        _STALE_AFTER_SECONDS,
        settings.RATE_LIMIT_WINDOW_SECONDS,
        settings.RATE_LIMIT_TIMEOUT_SECONDS,
    )


def _sweep_stale_entries(now: float) -> None:
    global _last_sweep
    if now - _last_sweep < _SWEEP_INTERVAL_SECONDS:
        return
    _last_sweep = now
    stale_after = _stale_after()
    stale_ips = [
        ip for ip, rec in _store.items()
        if now - rec["last_update"] > stale_after
    ]
    for ip in stale_ips:
        _store.pop(ip, None)


def _record_failure(ip: str, now: float) -> bool:
    """Record one failure for *ip*. Returns True if it is now blocked."""
    rec = _store.setdefault(
        ip, {"failures": [], "locked_until": None, "last_update": now}
    )
    window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
    rec["failures"] = [t for t in rec["failures"] if t > window_start]
    rec["failures"].append(now)
    rec["last_update"] = now

    if len(rec["failures"]) < settings.RATE_LIMIT_MAX_FAILURES:
        return False

    rec["locked_until"] = now + settings.RATE_LIMIT_TIMEOUT_SECONDS
    # Start clean once the block expires, rather than re-locking on the very
    # next failure because the same old timestamps are still in the window.
    rec["failures"] = []
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Block IPs that repeatedly fail on sensitive routes."""

    async def dispatch(self, request: Request, call_next):
        route_key = (request.method, request.url.path)

        # Fast path: not a protected route — pass straight through.
        if route_key not in PROTECTED_ROUTES:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        _sweep_stale_entries(now)

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
        # Successes are deliberately not recorded — see the module docstring.
        if response.status_code >= 400 and _record_failure(ip, time.time()):
            print(
                f"[RateLimit] IP {ip} blocked for "
                f"{settings.RATE_LIMIT_TIMEOUT_SECONDS}s after "
                f"{settings.RATE_LIMIT_MAX_FAILURES} failures within "
                f"{settings.RATE_LIMIT_WINDOW_SECONDS}s "
                f"on {request.method} {request.url.path}"
            )

        return response
