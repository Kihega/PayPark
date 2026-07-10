#!/usr/bin/env python3
"""
ParkiPay — CI workflow patch: promote develop → main via PR + auto-merge
==========================================================================
WHAT WAS BROKEN
----------------
Both .github/workflows/backend-ci.yml and mobile-ci.yml ended with a
`merge-to-main` job that did:

    git checkout main
    git merge --no-ff develop ...
    git push origin main          # ← directly pushes to main

Your `main` branch ruleset requires "Changes must be made through a
pull request" — so that job was *guaranteed* to fail with GH013 the
first time it ran, no matter who or what triggered it (that's the
exact error from your earlier push).

backend-ci.yml's `lint` job also had malformed YAML (steps missing
their `- name:` list markers / correctly nested under `steps:`),
which would break that job independently of the above.

WHAT THIS PATCH DOES
---------------------
1. Fixes the malformed `lint` job indentation in backend-ci.yml.
2. Replaces both `merge-to-main` jobs with a `promote-to-main` job
   that, once lint/security/test all pass on a push to `develop`:
     - opens a develop → main PR (or reuses one if it already exists)
     - calls `gh pr merge --auto --merge` to enable auto-merge on it
   This never pushes to main directly — GitHub itself performs the
   merge once the PR satisfies your ruleset's requirements, which is
   exactly the "no manual branch switch, merge once tests pass" flow
   you described.
3. Adds a `pull_request: branches: [main]` trigger to both CI
   workflows so lint/test also run *on the develop → main PR itself*
   — giving your ruleset actual PR-level checks to require (a check
   that only ran on `develop` can't be required on a PR into `main`).

STILL TO DO ON GITHUB (can't be done from a script — needs the UI):
---------------------------------------------------------------------
1. Repo Settings → General → confirm "Allow auto-merge" is checked
   (you mentioned you've already done this).
2. Repo Settings → Rules → Rulesets → your `main` ruleset →
   "Require status checks to pass" → add:
     - "Test (Jest + Prisma)"   (from backend-ci.yml)
     - "Test (Jest)"            (from mobile-ci.yml)
   These names will only appear as selectable options AFTER this
   patch has run once on a develop → main PR (GitHub needs to have
   seen the check at least once).
3. The GH_PAT secret needs `repo` + `workflow` scopes, which it
   already required for the old direct-push job — no change needed
   there, just confirm it's still valid.

USAGE
-----
Run from the repository root (the folder containing `.github/`):

    python3 patch_ci_promote_develop_to_main.py
"""
import os
import subprocess

ROOT = os.getcwd()


def path(*parts):
    return os.path.join(ROOT, *parts)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, text):
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def require_in(text, needle, filename):
    if needle not in text:
        raise SystemExit(
            f"\n✗ Anchor text not found verbatim in {filename} — aborting to avoid "
            f"a bad patch (the file may already be patched or has diverged).\n"
            f"  Looking for:\n{needle[:200]}\n"
        )


def git_commit(message):
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if result.returncode == 0:
        print("  (no changes to commit — skipping)")
        return
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT, check=True)
    print(f"  ✓ committed: {message.splitlines()[0]}")


def check_repo():
    if not os.path.isdir(path(".github", "workflows")):
        raise SystemExit(
            "Expected ./.github/workflows here — run this from the repo root."
        )
    if not os.path.isdir(path(".git")):
        raise SystemExit("Not a git repository. Run this from inside your git checkout.")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — backend-ci.yml: fix malformed lint job + swap merge job
# ═══════════════════════════════════════════════════════════════════════════
BACKEND_OLD_PR_TRIGGER = """  pull_request:
    branches: [develop]
    paths:
      - "backend/**"
"""
BACKEND_NEW_PR_TRIGGER = """  pull_request:
    branches: [develop, main]
    paths:
      - "backend/**"
"""

BACKEND_OLD_LINT = """  lint:
    name: Lint (ESLint)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
  uses: actions/checkout@v4

- name: Setup Node 20
  uses: actions/setup-node@v4
  with:
    node-version: "20"
    cache: npm
    cache-dependency-path: backend/package-lock.json

- name: Install dependencies
  working-directory: backend
  run: npm ci

- name: Run ESLint
  working-directory: backend
  run: npm run lint
"""
BACKEND_NEW_LINT = """  lint:
    name: Lint (ESLint)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: backend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint
"""

BACKEND_OLD_MERGE_JOB = """  # ── Merge develop → main (push only, all checks green) ───────────────────
  merge-to-main:
    name: Merge develop → main
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, security-audit, test]

    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_PAT }}

      - name: Configure git identity
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Merge develop into main
        run: |
          git checkout main
          git merge --no-ff develop -m "ci(backend): auto-merge develop → main [skip ci]"
          git push origin main
"""

BACKEND_NEW_MERGE_JOB = """  # ── Promote develop → main via PR + auto-merge (ruleset-compliant) ───────
  promote-to-main:
    name: Promote develop → main (PR + auto-merge)
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, security-audit, test]
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Open (or reuse) develop → main PR and enable auto-merge
        env:
          GH_TOKEN: ${{ secrets.GH_PAT }}
        run: |
          number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')

          if [ -z "$number" ]; then
            if gh pr create \\
              --base main --head develop \\
              --title "chore: promote develop → main" \\
              --body "Automated promotion — backend CI passed on develop @ ${{ github.sha }}."
            then
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            else
              echo "gh pr create failed (likely a race with mobile-ci's promote job) — re-checking..."
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            fi
          fi

          if [ -z "$number" ]; then
            echo "::error::Could not find or create a develop → main PR"
            exit 1
          fi

          echo "Using PR #$number"
          gh pr merge "$number" --auto --merge
"""


def step_01_backend_ci():
    print("\n[1/2] .github/workflows/backend-ci.yml")
    p = path(".github", "workflows", "backend-ci.yml")
    text = read(p)

    if "promote-to-main" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, BACKEND_OLD_PR_TRIGGER, "backend-ci.yml (pull_request trigger)")
    text = text.replace(BACKEND_OLD_PR_TRIGGER, BACKEND_NEW_PR_TRIGGER)

    require_in(text, BACKEND_OLD_LINT, "backend-ci.yml (lint job)")
    text = text.replace(BACKEND_OLD_LINT, BACKEND_NEW_LINT)

    require_in(text, BACKEND_OLD_MERGE_JOB, "backend-ci.yml (merge-to-main job)")
    text = text.replace(BACKEND_OLD_MERGE_JOB, BACKEND_NEW_MERGE_JOB)

    assert "git push origin main" not in text
    assert "promote-to-main" in text
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "ci(backend): fix malformed lint step + promote develop->main via PR/auto-merge "
        "instead of direct push (ruleset-compliant)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — mobile-ci.yml: swap merge job (lint job here was already valid)
# ═══════════════════════════════════════════════════════════════════════════
MOBILE_OLD_PR_TRIGGER = """  pull_request:
    branches: [develop]
    paths:
      - "mobile/**"
"""
MOBILE_NEW_PR_TRIGGER = """  pull_request:
    branches: [develop, main]
    paths:
      - "mobile/**"
"""

MOBILE_OLD_MERGE_JOB = """  # ── Merge develop → main (push only, all checks green) ───────────────────
  merge-to-main:
    name: Merge develop → main
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, type-check, test]

    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_PAT }}

      - name: Configure git identity
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Merge develop into main
        run: |
          git checkout main
          git merge --no-ff develop -m "ci(mobile): auto-merge develop → main [skip ci]"
          git push origin main
"""

MOBILE_NEW_MERGE_JOB = """  # ── Promote develop → main via PR + auto-merge (ruleset-compliant) ───────
  promote-to-main:
    name: Promote develop → main (PR + auto-merge)
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, type-check, test]
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Open (or reuse) develop → main PR and enable auto-merge
        env:
          GH_TOKEN: ${{ secrets.GH_PAT }}
        run: |
          number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')

          if [ -z "$number" ]; then
            if gh pr create \\
              --base main --head develop \\
              --title "chore: promote develop → main" \\
              --body "Automated promotion — mobile CI passed on develop @ ${{ github.sha }}."
            then
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            else
              echo "gh pr create failed (likely a race with backend-ci's promote job) — re-checking..."
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            fi
          fi

          if [ -z "$number" ]; then
            echo "::error::Could not find or create a develop → main PR"
            exit 1
          fi

          echo "Using PR #$number"
          gh pr merge "$number" --auto --merge
"""


def step_02_mobile_ci():
    print("\n[2/2] .github/workflows/mobile-ci.yml")
    p = path(".github", "workflows", "mobile-ci.yml")
    text = read(p)

    if "promote-to-main" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, MOBILE_OLD_PR_TRIGGER, "mobile-ci.yml (pull_request trigger)")
    text = text.replace(MOBILE_OLD_PR_TRIGGER, MOBILE_NEW_PR_TRIGGER)

    require_in(text, MOBILE_OLD_MERGE_JOB, "mobile-ci.yml (merge-to-main job)")
    text = text.replace(MOBILE_OLD_MERGE_JOB, MOBILE_NEW_MERGE_JOB)

    assert "git push origin main" not in text
    assert "promote-to-main" in text
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "ci(mobile): promote develop->main via PR/auto-merge instead of direct push "
        "(ruleset-compliant)"
    )


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay CI patch — promote develop -> main via PR + auto-merge")
    print("=" * 60)

    step_01_backend_ci()
    step_02_mobile_ci()

    print("\n" + "=" * 60)
    print("✓ Done. Review with `git log --oneline` / `git show`.")
    print("  Push this to a feature branch and open a PR (main is still protected).")
    print("\n  One-time GitHub UI steps still needed:")
    print("  1. Settings → General → confirm 'Allow auto-merge' is checked.")
    print("  2. Merge THIS patch's own PR first, so the new workflow exists on")
    print("     develop and main.")
    print("  3. After the next develop push runs the new 'promote-to-main' job")
    print("     once, its check names become selectable in your main ruleset ->")
    print("     'Require status checks to pass' -> add 'Test (Jest + Prisma)' and")
    print("     'Test (Jest)'. Until you do this, the develop->main PR auto-merges")
    print("     as soon as it's mergeable with no required checks enforced on it,")
    print("     so add this promptly if you want main gated on tests explicitly.")


if __name__ == "__main__":
    main()
