#!/usr/bin/env python3
"""
Generate the shared recurrence conformance fixture.

Recurrence expansion exists in two places: the canonical Python
implementation (app/common/utils/recurrence_expansion.py, served by
GET /event/range?expand=true) and the web client's own copy
(app/src/lib/utils.js), which is kept because it re-derives instantly when
filters or views change and refetching on every toggle would be a real
regression.

Two implementations can drift, and this project's have — twice. So the
Python one generates this fixture and the JavaScript one is tested against
it. A divergence becomes a failing test instead of two surfaces quietly
disagreeing about the same database.

The Android widget is deliberately *not* in this picture: it consumes
?expand=true and expands nothing itself, which is why its hand-ported Kotlin
implementation could be deleted outright.

Regenerate after any deliberate change to the recurrence rules:

    cd api && uv run python scripts/generate_conformance_fixture.py

...then run `npm test` in app/ and expect failures wherever the change was
intended. If nothing fails, the change did not do what you thought.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.common.utils.recurrence_expansion import (  # noqa: E402
    occurrences_in_range,
    resolve_timezone,
)

# UTC throughout. The fixture is about *rule semantics*, and a fixed offset
# keeps it reproducible on any machine — the JS side sets its own clock to
# match rather than depending on wherever the test happens to run.
TZ_NAME = "UTC"

OUTPUT = (
    Path(__file__).resolve().parent.parent.parent
    / "app" / "src" / "lib" / "__fixtures__" / "recurrence-conformance.json"
)


def epoch(year: int, month: int, day: int, hour: int = 9) -> int:
    return int(
        datetime(year, month, day, hour, 0, tzinfo=timezone.utc).timestamp()
    )


def build_cases() -> list[dict]:
    tz = resolve_timezone(TZ_NAME)
    cases = []

    ranges = {
        "month-five-years-in": (epoch(2026, 3, 1, 0), epoch(2026, 3, 31, 0)),
        "month-of-start": (epoch(2019, 1, 1, 0), epoch(2019, 1, 31, 0)),
        "three-day-window": (epoch(2019, 1, 7, 0), epoch(2019, 1, 9, 0)),
        "spanning-two-months": (epoch(2021, 7, 15, 0), epoch(2021, 8, 22, 0)),
        "past-every-end": (epoch(2030, 12, 1, 0), epoch(2030, 12, 31, 0)),
    }

    rules = []
    for rec_type in ("D", "W", "M", "Y"):
        for interval in (1, 2, 3, 5):
            day_options = (
                [None, "1010100", "0000011", "0100000"]
                if rec_type == "W"
                else [None]
            )
            for days in day_options:
                for end_type in ("N", "C", "U"):
                    for limit in (3, 50, 400):
                        rules.append(
                            {
                                "type": rec_type,
                                "interval": interval,
                                "days": days,
                                "endType": end_type,
                                "count": limit if end_type == "C" else None,
                                "until": (
                                    epoch(2026, 6, 30, 0)
                                    if end_type == "U"
                                    else None
                                ),
                            }
                        )

    # Anchor dates chosen to exercise the awkward cases as well as ordinary
    # ones: the 31st and Feb 29 are where monthly/yearly skip semantics
    # actually differ from clamping or rolling over.
    starts = [
        ("2019-01-07", epoch(2019, 1, 7)),
        ("2023-01-07", epoch(2023, 1, 7)),
        ("2026-01-07", epoch(2026, 1, 7)),
        ("2019-01-31", epoch(2019, 1, 31)),
        ("2020-02-29", epoch(2020, 2, 29)),
    ]

    for range_name, (range_start, range_end) in ranges.items():
        for rule in rules:
            for start_name, date_start in starts:
                date_end = date_start + 3600
                occurrences = occurrences_in_range(
                    date_start, date_end, rule, range_start, range_end, tz
                )
                cases.append(
                    {
                        "name": (
                            f"{rule['type']}/i{rule['interval']}"
                            f"/{rule['days'] or '-'}"
                            f"/{rule['endType']}{rule['count'] or ''}"
                            f"/from-{start_name}/over-{range_name}"
                        ),
                        "dateStart": date_start,
                        "dateEnd": date_end,
                        "recurrence": rule,
                        "rangeStart": range_start,
                        "rangeEnd": range_end,
                        "expected": occurrences,
                    }
                )

    return cases


def main() -> None:
    cases = build_cases()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "_comment": (
                    "GENERATED — do not edit by hand. Produced by "
                    "api/scripts/generate_conformance_fixture.py from the "
                    "canonical Python implementation. Regenerate after any "
                    "deliberate recurrence change."
                ),
                "timezone": TZ_NAME,
                "cases": cases,
            },
            indent=1,
        )
        + "\n"
    )
    non_empty = sum(1 for c in cases if c["expected"])
    print(f"Wrote {len(cases)} cases ({non_empty} with occurrences) to {OUTPUT}")


if __name__ == "__main__":
    main()
