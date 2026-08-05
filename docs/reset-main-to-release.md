# Resetting `main` to a single release commit

Replaces the whole history of `main` with one commit containing the current
state of `link/review-fixes`, tagged `v1.0.0`.

**Read the warnings before running anything.** This is irreversible from the
remote's point of view and it deletes information that other files in this
repository refer to.

---

## What this destroys

- **All 80 commits.** Every message, date and author. `git blame` will
  attribute every line in the project to one commit on one day.
- **The evidence behind `AI-DISCLOSURE.md`.** That file's percentages were
  measured with `git blame` against the real history, and it tells readers
  they can reproduce the figures themselves. After a squash they cannot.
  Either edit the file to say the history was squashed, or keep an archive
  branch (below) and point at it.
- **The cross-references in `review.md` and `next-steps-2026-08-01.md`.** These name commits and describe what changed
  when. The prose survives; the ability to check it does not.
- **Anything only reachable from the old commits.** If someone else has
  cloned or forked, their history and yours diverge permanently.

If any of that matters, do the "keep an archive" variant below. It costs one
extra branch and nothing else.

---

## Before you start

```bash
# 1. Make sure you are where you think you are.
git status
git log --oneline -1 link/review-fixes

# 2. Take a local backup ref. Free, and the only undo you get.
git branch backup/pre-squash-main main
git branch backup/pre-squash-review link/review-fixes

# 3. Make sure the working tree is clean.
git status --porcelain   # must print nothing
```

---

## Option A — squash, keeping the old history on an archive branch

Recommended. `main` becomes a single clean commit; the real history stays
reachable so the disclosure and reviews remain verifiable.

```bash
# Publish the current history under a name that will not be touched again.
git branch archive/history-pre-1.0.0 link/review-fixes
git push origin archive/history-pre-1.0.0

# Build a single commit containing exactly the current tree.
git checkout link/review-fixes
git checkout --orphan release-1.0.0     # no parent, same working tree
git add -A
git commit -m "release: v1.0.0

Self Calendar 1.0.0.

History before this point was squashed. The full development history is
preserved on the archive/history-pre-1.0.0 branch, including the commits
that AI-DISCLOSURE.md's measurements were taken from."

# Point main at it.
git branch -f main release-1.0.0
git checkout main
git branch -D release-1.0.0

# Tag it.
git tag -a v1.0.0 -m "Self Calendar 1.0.0"

# Push. --force-with-lease refuses if the remote moved since you last
# fetched, which is the difference between overwriting your own work and
# overwriting somebody else's.
git push --force-with-lease origin main
git push origin v1.0.0
```

---

## Option B — squash, discarding history entirely

Only if you are certain. Same as A without the archive branch:

```bash
git checkout link/review-fixes
git checkout --orphan release-1.0.0
git add -A
git commit -m "release: v1.0.0"
git branch -f main release-1.0.0
git checkout main
git branch -D release-1.0.0
git tag -a v1.0.0 -m "Self Calendar 1.0.0"
git push --force-with-lease origin main
git push origin v1.0.0
```

Then edit `AI-DISCLOSURE.md`: the "Reproduce the raw figures with `git
blame`" instruction is no longer true, and leaving it in makes the document
misleading rather than merely less useful.

---

## Verify before you trust it

```bash
git log --oneline main            # exactly one commit
git tag -l v1.0.0                 # the tag exists
git diff link/review-fixes main   # must be EMPTY — same tree, different history
```

That third command is the important one. If it prints anything, the squash
did not capture the state you meant and you should reset from
`backup/pre-squash-review` and start again.

---

## Cleaning up the development branches

Only after you have confirmed `main` is correct:

```bash
git push origin --delete link/review-fixes
git push origin --delete link/google-test

# Local copies
git branch -D link/review-fixes link/google-test
```

Keep `backup/pre-squash-*` locally until you are genuinely finished. They
cost nothing and they are the only way back.

---

## If you need to undo it

Only possible while your local backup refs still exist:

```bash
git branch -f main backup/pre-squash-main
git push --force-with-lease origin main
git push origin --delete v1.0.0     # if it was already pushed
git tag -d v1.0.0
```

Once those refs are gone and the remote has been garbage-collected, the old
commits are unrecoverable.

---

## A note on the release workflow

`ci/github-workflow-release.yml` refuses to run when the tag already exists.
Creating `v1.0.0` by hand here means the workflow **will not** cut a 1.0.0
release afterwards — which is correct, since you would be publishing a second
set of artefacts under a tag that already points somewhere.

To get 1.0.0 artefacts built by CI instead, skip the `git tag` step above and
let the workflow create the tag when `VERSION` lands on `main`. To publish
artefacts for a tag you created by hand, build them locally and attach them
to the release manually.
