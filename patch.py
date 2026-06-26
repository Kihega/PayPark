#!/usr/bin/env python3
"""
ParkiPay patch — paypark_patch5.py

Fixes the "content gets cut off on small/medium screens" issue across the
WHOLE app, not just the two forms touched in patch4.

What patch4 did:
  - Created mobile/utils/responsive.ts (scale / verticalScale / moderateScale)
  - Capped OS font-scaling globally in the root layout
  - Applied moderateScale() to fonts in admin.tsx and vehicles.tsx ONLY

What this patch does:
  Applies moderateScale() to every literal `fontSize: <number>` in every
  screen and shared component under mobile/app/ and mobile/components/
  (skipping files that don't have any, and skipping values that are
  already wrapped in moderateScale(...)). This is the single biggest lever
  for "auto resize content per screen" because text that doesn't shrink on
  small phones is what causes truncation/clipping/overlap — buttons and
  containers in this codebase are already mostly flex/percentage-based, so
  scaling the type itself is what makes everything else (badges, chips,
  rows, cards) reflow correctly without manual per-screen redesign.

  Files touched (only if they contain `fontSize:<number>`):
    mobile/app/(app)/admin.tsx        (any literals patch4 missed)
    mobile/app/(app)/vehicles.tsx     (any literals patch4 missed)
    mobile/app/(app)/home.tsx
    mobile/app/(app)/lookup.tsx
    mobile/app/(app)/history.tsx
    mobile/app/(app)/alerts.tsx
    mobile/app/(auth)/login.tsx
    mobile/components/ConfirmModal.tsx
    ...and any other .tsx file found under mobile/app/ or mobile/components/

  For each touched file, this patch:
    1. Adds `import { moderateScale } from '@/utils/responsive';` right
       after the last existing top-level import line, if not already present.
    2. Regex-replaces every `fontSize: 123` / `fontSize:123.5` with
       `fontSize: moderateScale(123)` (decimals preserved).
       Already-wrapped occurrences (`fontSize: moderateScale(...)`) are
       left untouched — safe to run twice.

  This patch does NOT touch fixed widths/heights of icon boxes, FABs, or
  modal sheets — those are container chrome, not content, and changing them
  blindly via regex risks breaking layouts in ways that are hard to verify
  without a device. Font scaling is the safe, high-impact fix; if specific
  screens still clip after this, send me those screens and I'll do a
  targeted layout patch for them.

Usage:
    python3 paypark_patch5.py
Requires patch4 (mobile/utils/responsive.ts) to already be applied.
"""
import os
import re
import sys

ROOT = os.getcwd()
IMPORT_LINE = "import { moderateScale } from '@/utils/responsive';"

FONT_SIZE_RE = re.compile(r'fontSize:\s*(\d+(?:\.\d+)?)\b(?!\s*[,}]?\s*\)|.*moderateScale)')
# Simpler, robust pattern: match `fontSize:` followed directly by a number
# (not by the word moderateScale). This is safe because once wrapped the
# text right after the colon is "moderateScale(", never a digit.
SAFE_FONT_SIZE_RE = re.compile(r'fontSize:\s*(\d+(?:\.\d+)?)\b')


def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, c):
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)


def ensure_import(content: str) -> str:
    if "from '@/utils/responsive'" in content:
        return content
    lines = content.split("\n")
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("import "):
            last_import_idx = i
    if last_import_idx == -1:
        # No imports found (unlikely) — just prepend
        return IMPORT_LINE + "\n" + content
    lines.insert(last_import_idx + 1, IMPORT_LINE)
    return "\n".join(lines)


def wrap_font_sizes(content: str) -> tuple[str, int]:
    count = 0

    def repl(m):
        nonlocal count
        num = m.group(1)
        count += 1
        return f"fontSize: moderateScale({num})"

    # Only replace occurrences not already followed by moderateScale(
    def safe_repl(m):
        start = m.start()
        # Look at the text right after the colon to see if it's already moderateScale
        after_colon = content[m.end(0):m.end(0) + 20]
        if after_colon.strip().startswith(""):
            pass
        return repl(m)

    new_content, n = SAFE_FONT_SIZE_RE.subn(repl, content)
    return new_content, n


def main():
    mobile_dir = os.path.join(ROOT, "mobile")
    responsive_path = os.path.join(mobile_dir, "utils", "responsive.ts")
    if not os.path.isfile(responsive_path):
        fail(
            "mobile/utils/responsive.ts not found. Run paypark_patch4.py first "
            "(it creates the responsive scaling helpers this patch depends on)."
        )

    targets = []
    for sub in ("app", "components"):
        base = os.path.join(mobile_dir, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith(".tsx") or fn.endswith(".ts"):
                    targets.append(os.path.join(dirpath, fn))

    if not targets:
        fail("No .tsx/.ts files found under mobile/app or mobile/components.")

    total_files_changed = 0
    total_fontsizes_wrapped = 0

    for path in sorted(targets):
        rel = os.path.relpath(path, ROOT)
        if path == responsive_path:
            continue
        content = read(path)
        if "fontSize:" not in content:
            continue

        # Skip if every fontSize is already wrapped (idempotent re-run)
        raw_matches = SAFE_FONT_SIZE_RE.findall(content)
        if not raw_matches:
            continue

        already_wrapped_pattern = re.compile(r'fontSize:\s*moderateScale\(')
        unwrapped_count = len(SAFE_FONT_SIZE_RE.findall(
            re.sub(already_wrapped_pattern, 'SKIP(', content)
        ))
        if unwrapped_count == 0:
            print(f"ℹ️  {rel}: all fontSize values already wrapped, skipping")
            continue

        new_content = ensure_import(content)
        new_content, n = wrap_font_sizes(new_content)

        if n == 0:
            continue

        write(path, new_content)
        total_files_changed += 1
        total_fontsizes_wrapped += n
        print(f"✅ {rel}: wrapped {n} fontSize value(s) in moderateScale()")

    print()
    print(f"🎉 Patch 5 applied: {total_files_changed} file(s) changed, "
          f"{total_fontsizes_wrapped} fontSize value(s) now responsive.")
    print()
    print("This patch is idempotent — safe to re-run after adding new screens;")
    print("already-wrapped fontSize values are left alone.")
    print()
    print("If a specific screen still clips content on a small device after")
    print("this, that screen likely has a fixed-height container (not just")
    print("font) that needs a manual layout fix rather than a blanket regex.")


if __name__ == "__main__":
    main()
