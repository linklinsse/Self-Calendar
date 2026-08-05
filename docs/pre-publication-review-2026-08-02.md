# Pre-publication review — Self Calendar

**Date:** 2026-08-02
**Branch:** `link/review-fixes` @ `31bf943`
**Question:** what should be cleaned up before this repository is made public?

Not another code-quality review — the two earlier review reports and
`review.md` cover that, and the substantive bugs they found are fixed. This
one asks a narrower question: *what will a stranger encounter, and what will
embarrass or endanger you once this is visible and permanent?*

Publication is one-way. Forks and clones persist after a repo is
re-privatised, and GitHub caches force-pushed commits. Everything below
assumes that.

---

## Blocking — do not publish without these

### B1. `*.keystore` is not gitignored

**The single most serious item here**, because it combines a missing safety
net with a document that actively walks you toward the hazard.

`docs/android-production-build.md` tells you to run `keytool -genkeypair
-keystore selfcalendar-release.keystore` and then says "check it is
ignored". It is not:

```
$ git check-ignore -v app/android/release.keystore
(no output — not ignored)
```

`app/android/.gitignore` is the standard Android template, which covers
`*.apk`, `*.aab`, `local.properties` and `build/` — but **not** keystores.
So the intended workflow is: generate a signing key in the repository, and
have nothing stop you committing it.

An app signing key in a public repo is unrecoverable in the strict sense.
Anyone can build and sign an APK that Android will treat as a legitimate
update to yours. Rotating means every existing install must uninstall and
lose its data.

**Fix — do this before anything else:**

```gitignore
# app/android/.gitignore
*.keystore
*.jks
keystore.properties
```

Then re-check with `git check-ignore -v app/android/release.keystore` and
confirm it prints a match.

### B2. `CLAUDE.md` is committed and is not about this project

64 lines of generic LLM-coaching instructions ("Don't assume. Don't hide
confusion. Surface tradeoffs.") sitting at the repository root. It is not
documentation of Self Calendar — it is configuration for an assistant.

Publishing it is not dangerous, but it is the first odd thing a visitor
finds, and it says nothing about the software. Either move it somewhere
scoped (`.claude/CLAUDE.md`, which tooling reads and humans ignore) or add
it to `.gitignore`. Given `AI-DISCLOSURE.md` now documents the AI
involvement properly and honestly, this file adds nothing a reader needs.

### B3. Run the secret audit again immediately before flipping the switch

It was run on 2026-08-02 and came back clean — no `github_pat_`/`ghp_`/
private-key patterns in history on any branch, no `.env` or keystore ever
committed, both templates carry the `change-me-use-openssl-rand-hex-32`
placeholder.

That result is only valid for the commit it ran against. Re-run the two
commands in `docs/going-public.md` as the last step before publishing, and
in particular *after* B1 (because fixing B1 is exactly when a keystore is
most likely to exist in the working tree).

---

## Should fix — visible quality problems

### S1. The documentation outnumbers the project

Thirteen tracked markdown files, ~3,100 lines. Five of them are
meta-documentation *about the development process*:

| File | Lines | What it is |
|---|---|---|
| ~~`self-calendar-code-review.md`~~ | 500 | first AI review — **deleted 2026-08-02** |
| ~~`code-review-2026-07-31.md`~~ | 344 | second AI review — **deleted 2026-08-02** |
| `review.md` | 318 | running maintenance notes |
| `next-steps-2026-08-01.md` | 200 | prioritised backlog |
| `AI-DISCLOSURE.md` | 106 | AI provenance |

That was 1,468 lines — nearly half the documentation — describing the
project's *history* rather than the project. A visitor opening the repo saw
two review reports about bugs that were already fixed, and would reasonably
conclude the code is riddled with them.

**The two review reports were deleted on 2026-08-02.** Their findings were
all addressed and are summarised in `review.md` §4 and §4b, which is the
part a contributor actually needs. The remaining suggestion below (moving
`review.md` and the roadmap into `docs/`) still stands.

This is worth being careful about, because the instinct to delete all of it
is also wrong. `review.md` and `next-steps` are genuinely useful to a
contributor, and `AI-DISCLOSURE.md` should stay prominent. The two
historical reviews are the problem: they describe a state the code is no
longer in.

**Suggested shape:**

- Keep at root: `README.md`, `LICENSE`, `AI-DISCLOSURE.md`, `VERSION`.
- Move to `docs/`: `review.md` (rename to `docs/maintenance-notes.md`),
  `next-steps-2026-08-01.md` (→ `docs/roadmap.md`).
- Move to `docs/archive/`: both code-review files, with a one-line header
  saying they are historical and their findings are fixed.
- The README's link list is currently ten items deep before a visitor
  reaches "what is this and how do I run it". Cut it to four.

### S2. `TODO` is a private scratchpad, published

```
Design:
- Event color is not send
- Event title not verry visible
- Caterories changes icon selections
- Add Theme unicorn
```

Fine as a personal note; less good as the public statement of what is
unfinished. It also duplicates `next-steps-2026-08-01.md`, which covers the
same ground properly.

Either convert these to GitHub Issues (you are enabling issues anyway, and
this is exactly what they are for), or fold them into the roadmap document
and delete the file.

**One of them is a real bug worth triaging first**, see S3.

### ~~S3~~ — DONE 2026-08-02. "Event color is not send" was a genuine gap

Traced it. `event.service.js:156` reads `raw.color ?? '#b8c9f4'` — but the
API has **no `color` field on events at all**, on either the model or the
schema. So `raw.color` is always undefined and every event falls back to
the same default unless it has a category.

That means per-event colour is not "not sent" — it is **not implemented
server-side**, and the client has code that looks like it supports it. The
comment on line 40 is accurate (`derived from category, not stored in API`)
but line 156 contradicts it.

Decide which is true and make the code say so: either add `color` to the
event model (needs a migration, which now exists) or delete the dead
fallback so nobody else spends an hour on it. Ten-minute job either way.

### ~~S4~~ — DONE 2026-08-02. A stale comment described the opposite of reality

`api/app/services/obj_category_service.py:99`:

> `# ObjEventModel.category_id has no foreign key yet (see the TODO on the model)`

It does have one, as of the `be83bce50e32` migration, and the TODO it
refers to is gone. This is the second-worst kind of comment — confidently
wrong about a security-relevant invariant. The service-level cleanup it
guards is still correct and worth keeping; only the rationale needs
rewriting.

Worth a `git grep -n "no foreign key\|TODO"` pass for others like it.

### ~~S5~~ — placeholders added 2026-08-02; real images still needed

The README opens with a competent paragraph of prose describing a
*calendar application*, and shows nothing. For a UI project this is the
single highest-return item in this document: most visitors decide in
seconds whether to keep reading.

Two or three screenshots (month view, event editor, the Android widget) in
`docs/img/`, embedded near the top. Nothing else here will affect how the
project is received as much.

---

## Worth doing — polish and community

### W1. Missing community health files

None of these exist:

| File | Why it matters here |
|---|---|
| `SECURITY.md` | **Most important of the four.** This app handles passwords, JWTs and personal calendar data. Without it, someone finding a vulnerability has no private channel and may open a public issue. One paragraph and an email address. |
| `CONTRIBUTING.md` | Even just "this is a personal project, issues may go unanswered, PRs welcome but I may be slow" — that is more respectful than silence. |
| `CHANGELOG.md` | You now have a version and a release workflow. A changelog is the natural companion. |
| `CODE_OF_CONDUCT.md` | Optional for a small project; GitHub offers a template. |

### W2. No issue templates

`.github/ISSUE_TEMPLATE/` does not exist. With issues enabled on a
self-hosted app, most reports will be deployment problems — and the two
that will dominate are already known and documented: the `DB_URL`-outside-
the-volume trap and CORS misconfiguration. A bug template that asks for
version, deployment method and API logs will save you repeating yourself.

Also note `.github/` will not exist at all until the workflows are
installed, so this can land in the same commit.

### W3. Neither workflow is installed

`ci/github-workflow-ci.yml` and `ci/github-workflow-release.yml` are both
correct and both inert, because the tokens used had no `workflow` scope. A
public repo with 118 API tests and 9,045 app tests and **no visible CI
badge** looks untested to a visitor, which is the opposite of the truth.

Install both, then add the badge to the README. Actions minutes are free for
public repos.

### W4. Lint baselines are large and advisory

`ruff`: 94 findings. `svelte-check`: 505 errors across 37 files (mostly
implicit `any` from checking JS under TS rules). Both are `continue-on-error`
in CI, which is the right call — starting red teaches everyone to ignore it.

But a public repo invites people to read the code, and `npm run check`
printing 505 errors is a bad first impression regardless of how benign they
are. Clearing `ruff` is genuinely quick (`ruff check --fix` handles 81 of
94). The svelte-check baseline is a bigger job; consider relaxing
`checkJs` in `jsconfig.json` instead of pretending to a strictness the
project has not adopted.

### W5. Commit history quality

If you squash to a single `v1.0.0` commit (per
`docs/reset-main-to-release.md`), this is moot. If you keep history, be
aware the early commits read `a tester` ×4, `test`, `testin`, `t`, `better`,
`better?`, `vibe coding`. Harmless, but visible.

---

## Deliberately not flagged

Things that look like problems and are not:

- **`print()` in `app.py` and `db_connection.py`.** These are startup
  diagnostics on a self-hosted app where the operator is reading the
  container log. A logger would be more correct and no more useful.
- **No `.dockerignore`.** Worth adding eventually; affects build time, not
  correctness or perception.
- **The `docs/` procedure files** (`going-public`, `reset-main`,
  `android-production-build`). These are operator documentation and belong
  in a public repo.
- **`python-dateutil`** — checked, it is genuinely used
  (`relativedelta` in the recurrence service). Not a stale dependency.

---

## The honest caveat

Everything above is about presentation and hygiene. The substantive risk in
this repository is unchanged and is stated plainly in
`next-steps-2026-08-01.md`:

**No Android code in this branch has ever run on hardware.** Not the widget's
token-refresh path, not the device-calendar export, not the cold-start deep
link. The release workflow will happily build an APK of it.

Publishing does not make that worse — but shipping an APK to strangers does.
`docs/android-production-build.md` has the on-device test list. Work through
it before attaching an APK to a public release, or say clearly in the release
notes that the Android build is untested.

---

## Suggested order

1. **B1** — gitignore keystores. Two minutes, and everything else can wait
   behind it.
2. **B2** — remove or relocate `CLAUDE.md`.
3. **S4, S3** — the stale comment and the colour gap. Both small, both
   things a reader will trip on.
4. **S1, S2** — restructure the docs, retire `TODO`.
5. **S5** — screenshots. Highest return on how the project is received.
6. **W1, W2** — `SECURITY.md` first, then the rest.
7. **W3** — install the workflows, add the badge.
8. **B3** — re-run the secret audit as the final step before flipping to
   public.
9. Then `docs/going-public.md` for the settings themselves.

Items 1–3 are under an hour. Items 4–7 are an afternoon. None of it is
blocked on anything else.
