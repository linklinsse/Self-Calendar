# AI disclosure

Self Calendar was started by hand and finished with substantial help from
Claude (Anthropic). This file says what that means in practice, because
"AI-assisted" covers everything from autocomplete to writing the whole thing,
and those are not the same claim.

## The short version

The project began in February 2026 as hand-written code — the FastAPI
backend, the data model, the permission scheme. From the end of March 2026
onward it was developed with AI assistance, first through Claude Code and
later through longer review-and-fix sessions. The Svelte frontend, the
Android widget, the Google Calendar importer, the test suites and most of
the documentation were written that way.

**Roughly 20% of the current code is hand-written and roughly 80% is
AI-generated or AI-assisted**, measured by surviving lines. See below for how
that number was reached and why it undersells the human part.

## Where the number comes from

Measured with `git blame` across the whole tracked tree, excluding lockfiles,
binary assets and generated fixtures — 16,958 non-blank lines at the time of
writing. A small share predates the first commit that mentions Claude
(2026-03-31); most of the rest is split between the 2026-07/08 review-and-fix
sessions and the maintainer's own commits, which account for the bulk of the
total.

That last part is the reason the headline number is an estimate rather than
a measurement. Many of the maintainer's own commits were themselves written
with Claude Code — one of them says so in its message — and git records who
committed, not who or what produced each line. The ~20% figure is the
maintainer's own estimate of the hand-written portion of those commits.

These figures were measured against the real development history before `main`
was squashed to a single release commit. The commits they were measured from
are no longer reachable, so the raw figures can no longer be reproduced with
`git blame` — this section is now a record of the measurement, not a
repeatable procedure.

## What "20% human" does not capture

Line count is a poor proxy for authorship, and it flatters the AI side in
several ways worth stating plainly:

- **Every design decision is human.** The data model, the R/W/O permission
  scheme, the recurrence representation, the choice to store timestamps, the
  decision to self-host — none of that came from a model.
- **Every task was chosen by a human.** The AI work in this repository was
  directed: fix this, review that, migrate the database. It did not decide
  what to build.
- **AI-written code is verbose.** Much of the ~80% is tests (over 9,000
  assertions), documentation and explanatory comments — categories where
  volume is cheap. The hand-written 20% is disproportionately core logic.
- **All of it was accepted by a human.** Code that was wrong got rejected or
  fixed. That review work leaves no trace in a line count.

Conversely, one thing the number *does* honestly capture: a person reading
this repository will find that most of what they read was drafted by a model.
That is what the disclosure is for.

## What was AI-assisted, specifically

Written primarily with Claude:

- The SvelteKit frontend (`app/src/`)
- The Android widget and Capacitor plugins (`app/android/`)
- The Google Calendar importer (`api/scripts/import_google_calendar.py`)
- The test suites (`api/tests/`, `app/src/lib/*.test.js`)
- Database migrations (`api/migrations/`)
- Most documentation, including this file

Written primarily by hand:

- The initial FastAPI application structure and data model
- The permission model's design
- The product itself: what it is, what it does, what it refuses to do

Reviewed, corrected and directed by a human throughout: all of it.

## If you are evaluating this project

Use it, fork it, learn from it — it is MIT licensed. But treat the AI
provenance as a reason to read before you trust, not as a reason to dismiss.
The test suites are the honest record of what has been verified and what has
not.
