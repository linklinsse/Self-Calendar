# Making the repository public

Settings to apply when publishing Self Calendar, in the order they should be
done.

---

## Read this first: branches cannot be hidden

**GitHub has no setting that hides branches from viewers of a public
repository.** Anyone can list every branch, browse its files, and read every
commit on it, at `/branches` or by switching the branch dropdown. There is no
per-branch visibility control, no "private branch" feature, and no plan for
one. Branch protection rules control *who can write*, not who can look.

So "public repo, dev branches hidden" is not a configuration — it needs a
different arrangement. Three that actually work:

**1. Delete the dev branches (simplest, recommended here).**
Squash everything into `main` and remove `link/review-fixes` and
`link/google-test`. `docs/reset-main-to-release.md` has the commands. After
that there is nothing to hide, because there is only `main`.

The cost: development history disappears from public view. Note that
`AI-DISCLOSURE.md` invites readers to verify its figures with `git blame`, so
if you squash, either keep an archive branch (which is then public too) or
edit that file to say the history was squashed.

**2. Develop in a separate private repository.**
Keep a private `Self-Calendar-dev` with all branches, and push only release
commits to the public one. Total control, and the overhead of two remotes
and a manual promotion step every release.

**3. Accept that branches are visible.**
Most open-source projects work this way. Feature branches being readable is
normal and rarely a problem — as long as nothing sensitive was ever committed
(see the audit below, which you must do regardless).

Pick one before making the repo public. Going public first and cleaning up
after does not work: anything that was briefly visible may have been cloned,
cached by GitHub, or indexed.

---

## Before flipping the switch: audit for secrets

Public means public *including history*. Every commit on every branch becomes
readable, permanently, and GitHub caches force-pushed commits for a while
even after they are gone from any branch.

```bash
# Anything that looks like a token or key, across all history
git log --all -p | grep -nEi 'github_pat_|ghp_|BEGIN [A-Z ]*PRIVATE KEY|SECRET_KEY *= *["'"'"']|password *= *["'"'"']' | head -50

# Files that should never have been committed
git log --all --name-only --format='' | sort -u | grep -Ei '\.env$|\.keystore$|\.jks$|credentials|client_secret'
```

Specific things to confirm for this repository:

| Item | Expected |
|---|---|
| `conf/.env` | never committed — only `.env.template` |
| `api/conf/.env` | never committed |
| Any `*.keystore` / `*.jks` | never committed |
| `SECRET_KEY` in templates | placeholder (`change-me…`), never a real value |
| Google OAuth `credentials.json` / `token.json` | never committed |

**If a real secret is found in history, rotate it — do not just delete the
commit.** Removing it from history does not un-leak it; assume anything ever
pushed has been read.

**This audit was run against the repository on 2026-08-02 and came back
clean:**

- no `github_pat_` / `ghp_` / private-key patterns anywhere in history
- no `.env`, `.keystore`, `.jks`, `credentials` or `client_secret` file ever
  committed on any branch
- both `.env.template` files carry the `change-me-use-openssl-rand-hex-32`
  placeholder, not a real key

The GitHub tokens used during development were pasted into a chat transcript
rather than committed, and were rotated daily. Re-run the commands above
before publishing anyway — the result is only valid as of the commit it was
run against.

---

## Repository settings

**Settings → General → Danger Zone → Change visibility → Public.**

Then, on the same Settings page:

### General

| Setting | Value | Why |
|---|---|---|
| Issues | **on** | as requested |
| Pull requests → Allow merge commits | on | |
| Pull requests → Allow squash merging | on | keeps `main` linear |
| Pull requests → Allow rebase merging | off | one merge style is easier to reason about |
| Automatically delete head branches | **on** | merged branches disappear on their own, which is most of what "hide dev branches" was after |
| Discussions | off unless you want them | another inbox to ignore |
| Wikis | off | `docs/` and the READMEs are in-repo and versioned; a wiki is a second, unversioned source of truth |
| Projects | off unless used | |
| Preserve this repository | optional | Arctic Code Vault archiving |

### Features worth enabling for a public repo

**Settings → Code security:**

| Setting | Value | Why |
|---|---|---|
| Dependency graph | on | free, and required by the next two |
| Dependabot alerts | **on** | tells you when a dependency has a known CVE |
| Dependabot security updates | on | opens the PR for you |
| Secret scanning | **on** | free for public repos, and it catches the exact mistake this project has already brushed against |
| Push protection | **on** | blocks a commit containing a recognised token *before* it lands |

Secret scanning and push protection are the two most valuable settings here.
Turn them on.

---

## Branch protection for `main`

**Settings → Rules → Rulesets → New branch ruleset**, targeting `main`:

- **Restrict deletions** — on
- **Require a pull request before merging** — on
  - Required approvals: `0` if you are the only maintainer. Requiring your
    own approval on a solo project just teaches you to click past it.
  - Dismiss stale approvals on push: on
- **Require status checks to pass** — on, once CI is installed
  - Select the `api` and `app` checks from `ci.yml`
- **Block force pushes** — on

**Do this *after* the `main` squash, not before.** "Block force pushes" will
prevent exactly the force-push that `docs/reset-main-to-release.md` performs.

---

## What to do about the existing dev branches

Following option 1 above:

```bash
# Only after main is squashed and verified — see docs/reset-main-to-release.md
git push origin --delete link/review-fixes
git push origin --delete link/google-test
git branch -D link/review-fixes link/google-test
```

With "Automatically delete head branches" enabled, future PR branches clean
themselves up on merge, so this stays manageable without further thought.

---

## Before you announce it

- **`LICENSE` is present** — MIT. Without it, "public" does not grant anyone
  the right to use the code.
- **`AI-DISCLOSURE.md` is accurate.** Especially the `git blame` instruction
  if you squashed.
- **The README's first screen explains what this is** and that it is
  self-hosted.
- **Add repository topics** (About → gear): `calendar`, `self-hosted`,
  `fastapi`, `svelte`, `capacitor`, `sqlite`. This is how people find it.
- **Set the About description and, if you have one, a demo URL.**
- **Consider pinning `next-steps-2026-08-01.md` in the README.** It is an
  honest account of what is unfinished, which is worth more to a prospective
  contributor than a feature list.

---

## Things a public repo changes that are easy to forget

- **GitHub Actions minutes are free for public repos.** Your CI cost drops to
  zero.
- **Forks are permanent.** Someone forking today keeps that copy even if you
  later delete or re-privatise the original.
- **Issues invite work.** Consider a short `CONTRIBUTING.md`, or say plainly
  in the README that this is a personal project and issues may go unanswered.
  Both are fine; silence with an open issue tracker is what frustrates people.
- **Re-privatising does not undo publication.** Clones, forks and caches
  persist. Treat going public as one-way.
