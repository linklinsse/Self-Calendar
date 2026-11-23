from datetime import datetime, timezone

from pydantic import Field
from typing import Annotated

CommonFieldColor = Annotated[
    str | None, Field(default=None, pattern="^#(?:[0-9a-fA-F]{3}){1,2}$")
]
CommonFieldTitle = Annotated[str, Field(max_length=255)]
# Unbounded description fields + no request body size limit is an easy
# storage-exhaustion vector on a self-hosted SQLite instance.
CommonFieldDescription = Annotated[str | None, Field(default=None, max_length=2000)]
# Free-text event fields (address, reminder). The model already declared 255,
# but SQLite does not enforce VARCHAR lengths and PATCH bypassed it entirely.
CommonFieldShortText = Annotated[str | None, Field(default=None, max_length=255)]
# A category icon is a single emoji, but one emoji can be several code points
# (skin tone, ZWJ sequences, flags) — 16 leaves room for those.
CommonFieldIcon = Annotated[str | None, Field(default=None, max_length=16)]

# Unix timestamps are stored as bare integers, but every consumer turns them
# into datetimes (recurrence expansion, compute_estimated_end, the clients),
# and Python's datetime stops at year 9999. An event dated past that was an
# HTTP 500 on its own creation — and, worse, on every later
# `GET /event/range?expand=true` touching its calendar, so one member with
# Write access could break the view (and the Android widget) for everyone
# sharing it. The bounds leave room on both sides for timezone offsets and
# for stepping a recurrence forward without leaving datetime's range.
TIMESTAMP_MIN = int(datetime(1000, 1, 1, tzinfo=timezone.utc).timestamp())
TIMESTAMP_MAX = int(datetime(5000, 1, 1, tzinfo=timezone.utc).timestamp())
CommonFieldTimestamp = Annotated[int, Field(ge=TIMESTAMP_MIN, le=TIMESTAMP_MAX)]
