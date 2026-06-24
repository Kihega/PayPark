#!/usr/bin/env python3
"""
Patch: fix duplicated /api/api/... path (404 "Endpoint not found")

Root cause (confirmed from device logs):
  [ParkiPay] API_BASE_URL -> http://localhost:8000/api
  [API] POST http://localhost:8000/api/api/auth/login/   <-- doubled
  POST /api/api/auth/login/ 404                            <-- server log

mobile/.env has EXPO_PUBLIC_API_URL set WITH a trailing /api
(e.g. http://localhost:8000/api). Every call site in mobile/services/api.ts
and every entry in API_ROUTES already starts with '/api/...', so:

    axios baseURL ('.../8000/api')  +  request path ('/api/auth/login/')
    = '.../8000/api/api/auth/login/'   -> 404, route doesn't exist

This is an easy mistake to make again (it looks correct at a glance), so
this patch fixes it at the SOURCE rather than just telling you to edit
.env: API_BASE_URL is normalized to always strip any trailing /api,
regardless of what's in .env, the emulator fallback, or the production
constant. That makes the bug structurally impossible going forward.

Run from the REPO ROOT (the directory containing backend/ and mobile/):
    python3 patch_fix_duplicate_api_path.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT       = Path(".")
MOBILE     = ROOT / "mobile"
API_CONST  = MOBILE / "constants" / "api.ts"


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def main() -> None:
    if not API_CONST.exists():
        fail(f"{API_CONST} not found — run this from the repo root.")

    src = API_CONST.read_text(encoding="utf-8")
    original = src

    old_block = (
        "export const API_BASE_URL: string =\n"
        "  // Priority 1: explicit override from .env (physical device / staging / prod)\n"
        "  process.env.EXPO_PUBLIC_API_URL ??\n"
        "  // Priority 2: auto-detect for simulators/emulators in dev mode\n"
        "  (__DEV__ ? getLocalDevUrl() : PRODUCTION_API_URL);\n"
    )
    if old_block not in src:
        fail(
            "Could not find the expected API_BASE_URL block — the file may "
            "already be patched, or its structure changed. Aborting, no "
            "changes made."
        )

    new_block = (
        "// Strip a trailing slash AND a trailing /api segment, however the\n"
        "// value was written (with/without protocol slash, with/without a\n"
        "// final slash). This makes it impossible to end up with the\n"
        "// '/api/api/...' duplication bug: every route in API_ROUTES (and\n"
        "// every call in services/api.ts) already starts with '/api/...',\n"
        "// so API_BASE_URL must always be just '<scheme>://<host>:<port>'\n"
        "// with NO /api suffix — whether it came from .env, the emulator\n"
        "// fallback, or the production constant.\n"
        "function stripApiSuffix(url: string): string {\n"
        "  return url.replace(/\\/+$/, '').replace(/\\/api$/i, '');\n"
        "}\n"
        "\n"
        "export const API_BASE_URL: string = stripApiSuffix(\n"
        "  // Priority 1: explicit override from .env (physical device / staging / prod)\n"
        "  process.env.EXPO_PUBLIC_API_URL ??\n"
        "  // Priority 2: auto-detect for simulators/emulators in dev mode\n"
        "  (__DEV__ ? getLocalDevUrl() : PRODUCTION_API_URL),\n"
        ");\n"
    )
    src = src.replace(old_block, new_block)

    # Also tighten the doc comment + .env.example guidance so the mistake
    # is harder to make again: be explicit that /api must NOT be included.
    old_doc_line = (
        " *   3. Set EXPO_PUBLIC_API_URL=http://<YOUR_LAN_IP>:8000\n"
    )
    new_doc_line = (
        " *   3. Set EXPO_PUBLIC_API_URL=http://<YOUR_LAN_IP>:8000\n"
        " *      (host:port ONLY — do NOT add /api; every route already\n"
        " *      includes it, and API_BASE_URL strips a trailing /api\n"
        " *      automatically if you add it anyway)\n"
    )
    if old_doc_line in src:
        src = src.replace(old_doc_line, new_doc_line)

    if src == original:
        fail("No changes were made — patch did not match expected source.")

    API_CONST.write_text(src, encoding="utf-8")
    print(f"✅ Patched {API_CONST}")

    # Also patch mobile/.env.example so the documented example can't mislead
    # anyone into adding /api either.
    env_example = MOBILE / ".env.example"
    if env_example.exists():
        env_src = env_example.read_text(encoding="utf-8")
        env_original = env_src
        env_src = re.sub(
            r"EXPO_PUBLIC_API_URL=http://192\.168\.1\.42:8000/api",
            "EXPO_PUBLIC_API_URL=http://192.168.1.42:8000",
            env_src,
        )
        env_src = re.sub(
            r"EXPO_PUBLIC_API_URL=https://parkipay-api\.onrender\.com/api",
            "EXPO_PUBLIC_API_URL=https://parkipay-api.onrender.com",
            env_src,
        )
        if env_src != env_original:
            env_example.write_text(env_src, encoding="utf-8")
            print(f"✅ Patched {env_example} (removed stray /api suffix from example)")
        else:
            print(f"ℹ️  {env_example} already clean — no /api suffix found.")
    else:
        print(f"⚠️  {env_example} not found — skipping.")

    # ── Commit ───────────────────────────────────────────────────────────
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("ℹ️  Nothing to commit.")
        return

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "fix(mobile): strip trailing /api from API_BASE_URL to prevent "
            "/api/api/... 404s when EXPO_PUBLIC_API_URL includes /api",
        ],
        check=True,
    )
    print("✅ Committed")
    print("\nNext: this repo's main branch is protected — push to a branch and PR:")
    print("    git checkout -b fix/duplicate-api-path")
    print("    git push origin fix/duplicate-api-path")
    print(
        "\nAlso double-check your LOCAL mobile/.env file (not .env.example) —"
        "\nif EXPO_PUBLIC_API_URL there still has a trailing /api, this patch"
        "\nnow strips it automatically, but you may want to clean it up for"
        "\nclarity anyway."
    )


if __name__ == "__main__":
    main()
