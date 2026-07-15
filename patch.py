#!/usr/bin/env python3
"""
ParkiPay — patch: fix missing DIRECT_URL (Prisma P1012 in CI)
=================================================================
WHAT WAS BROKEN
----------------
backend/prisma/schema.prisma requires BOTH:
    url       = env("DATABASE_URL")
    directUrl = env("DIRECT_URL")

(the standard Supabase + Prisma pattern: DATABASE_URL points at the
pgbouncer transaction pooler on port 6543 for normal app queries,
DIRECT_URL points at the direct connection on port 5432, which
`prisma migrate` needs because migrations don't work reliably through
a transaction pooler.)

The backend CI test job's `env:` block only set DATABASE_URL, so
`npx prisma migrate deploy` failed schema validation with:
    Error: Environment variable not found: DIRECT_URL.

backend/.env.example didn't document DIRECT_URL at all either, so
anyone setting up a fresh Supabase project from that template would
hit the same error locally.

WHAT THIS PATCH DOES
----------------------
1. .github/workflows/backend-ci.yml — adds DIRECT_URL to the `test`
   job's env block. CI's Postgres is a plain service container with
   no pooler, so DIRECT_URL is set to the same connection string as
   DATABASE_URL there — there's nothing to distinguish in that
   environment.
2. backend/.env.example — adds a documented DIRECT_URL line next to
   DATABASE_URL, pointing at Supabase's direct (non-pooled, port
   5432) connection host, with a comment on why both are needed.

USAGE
-----
Run from the repository root (the folder containing `backend/` and
`.github/`):

    python3 patch_fix_direct_url.py

AFTER RUNNING — action needed on your side (not scriptable):
----------------------------------------------------------------
Set DIRECT_URL as a real environment variable wherever DATABASE_URL
is already set for local/Render use:
  - Locally: add DIRECT_URL=... to backend/.env (get the value from
    Supabase → Settings → Database → Connection string → "URI" under
    the *non-pooled* / "Direct connection" tab — port 5432, NOT 6543).
  - Render: add DIRECT_URL as an environment variable in the service
    settings, same value.
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
    if not os.path.isdir(path("backend")) or not os.path.isdir(path(".github")):
        raise SystemExit(
            "This doesn't look like the ParkiPay repo root "
            "(expected ./backend and ./.github). Run from the repo root."
        )
    if not os.path.isdir(path(".git")):
        raise SystemExit("Not a git repository. Run this from inside your git checkout.")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — backend-ci.yml: add DIRECT_URL to the test job env
# ═══════════════════════════════════════════════════════════════════════════
CI_OLD_ENV = """    env:
      NODE_ENV:     test
      DATABASE_URL: postgresql://parkipay:parkipay@localhost:5432/parkipay_test
      JWT_SECRET:   ci-test-secret-not-for-production"""

CI_NEW_ENV = """    env:
      NODE_ENV:     test
      # CI's Postgres is a plain service container with no pooler, so
      # DIRECT_URL and DATABASE_URL point at the same place here —
      # only real Supabase environments need them to differ (see
      # backend/.env.example).
      DATABASE_URL: postgresql://parkipay:parkipay@localhost:5432/parkipay_test
      DIRECT_URL:   postgresql://parkipay:parkipay@localhost:5432/parkipay_test
      JWT_SECRET:   ci-test-secret-not-for-production"""


def step_01_ci_direct_url():
    print("\n[1/2] .github/workflows/backend-ci.yml — add DIRECT_URL to test job env")
    p = path(".github/workflows/backend-ci.yml")
    text = read(p)

    if "DIRECT_URL" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, CI_OLD_ENV, "backend-ci.yml (test job env)")
    text = text.replace(CI_OLD_ENV, CI_NEW_ENV)

    assert "DIRECT_URL" in text
    write(p, text)
    print(f"  patched {p}")
    git_commit("ci(backend): add missing DIRECT_URL to test job env (fixes Prisma P1012)")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — backend/.env.example: document DIRECT_URL
# ═══════════════════════════════════════════════════════════════════════════
ENV_OLD = """# ── Database (Supabase pooler — use port 6543, not 5432) ─────────────────────
# Settings → Database → Connection string → URI (Transaction pooler)
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"""

ENV_NEW = """# ── Database (Supabase) ───────────────────────────────────────────────────────
# Prisma needs BOTH of these — see backend/prisma/schema.prisma's
# `url` / `directUrl`. Using the pooler for DATABASE_URL and the
# direct connection for DIRECT_URL is Supabase's recommended setup:
# app queries go through pgbouncer, but `prisma migrate` needs a
# direct (non-pooled) connection to work reliably.
#
# DATABASE_URL — pooler, port 6543
#   Settings → Database → Connection string → URI (Transaction pooler)
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
#
# DIRECT_URL — direct connection, port 5432 (used only for migrations)
#   Settings → Database → Connection string → URI (Direct connection)
DIRECT_URL=postgresql://postgres.[ref]:[password]@aws-0-eu-west-1.supabase.co:5432/postgres"""


def step_02_env_example():
    print("\n[2/2] backend/.env.example — document DIRECT_URL")
    p = path("backend/.env.example")
    text = read(p)

    if "DIRECT_URL" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, ENV_OLD, "backend/.env.example")
    text = text.replace(ENV_OLD, ENV_NEW)

    assert "DIRECT_URL" in text
    write(p, text)
    print(f"  patched {p}")
    git_commit("backend: document DIRECT_URL in .env.example alongside DATABASE_URL")


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay patch — fix missing DIRECT_URL (Prisma P1012)")
    print("=" * 60)

    step_01_ci_direct_url()
    step_02_env_example()

    print("\n" + "=" * 60)
    print("✓ Done. Review with `git log --oneline` / `git show`.")
    print("  Push to a feature branch and open a PR (main is still protected).")
    print("\n  Still needed on your side (can't be scripted):")
    print("  - Add DIRECT_URL to backend/.env locally (Supabase dashboard ->")
    print("    Settings -> Database -> Connection string -> Direct connection,")
    print("    port 5432 — NOT the pooler on 6543).")
    print("  - Add DIRECT_URL as an env var on Render too, same value.")


if __name__ == "__main__":
    main()
