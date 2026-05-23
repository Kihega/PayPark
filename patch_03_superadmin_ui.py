#!/usr/bin/env python3
"""
ParkiPay Hotfix 3 — Fix 2 remaining TypeScript errors in lookup.tsx

  Error 1: `lookupState === 'generating'` inside isLoading else-branch —
           TypeScript narrows out 'generating' there, so the comparison
           appears unreachable. Fix: compute `verifyLabel` before JSX.

  Error 2: MaterialCommunityIcons name="car-question" — not a valid glyph.
           Fix: replace with "car-search-outline".

Run:
    python3 paypark_hotfix3.py /home/kali/PayPark
"""
import sys
from pathlib import Path

def find_root(arg=None):
    if arg:
        return Path(arg).resolve()
    for base in [Path.cwd(), Path('/home/kali'), Path('/home/kali/PayPark')]:
        for suf in ['', 'PayPark-main']:
            p = base / suf
            if (p / 'backend' / 'prisma' / 'schema.prisma').exists():
                return p
    sys.exit('Pass path: python3 paypark_hotfix3.py /home/kali/PayPark')

root   = find_root(sys.argv[1] if len(sys.argv) > 1 else None)
target = root / 'mobile' / 'app' / '(app)' / 'lookup.tsx'

if not target.exists():
    sys.exit(f'Not found: {target}')

txt = target.read_text(encoding='utf-8')
orig = txt

# ── Fix 1: car-question → car-search-outline ──────────────────────────────────
txt = txt.replace('name="car-question"', 'name="car-search-outline"')

# ── Fix 2: narrowing issue — add verifyLabel before JSX ───────────────────────
# Replace the isLoading line with isLoading + verifyLabel
OLD_DERIVED = "  const isLoading  = lookupState === 'loading' || lookupState === 'generating';"
NEW_DERIVED = (
    "  const isLoading   = lookupState === 'loading' || lookupState === 'generating';\n"
    "  const verifyLabel = (lookupState as string) === 'generating' ? 'GENERATING BILL...' : 'VERIFY VEHICLE';"
)

# Handle slight whitespace variations
import re
txt = re.sub(
    r"const isLoading\s+=\s+lookupState === 'loading' \|\| lookupState === 'generating';",
    "const isLoading   = lookupState === 'loading' || lookupState === 'generating';\n"
    "  const verifyLabel = (lookupState as string) === 'generating' ? 'GENERATING BILL...' : 'VERIFY VEHICLE';",
    txt
)

# Replace inline comparison in JSX with pre-computed label
txt = txt.replace(
    "{lookupState === 'generating' ? 'GENERATING BILL...' : 'VERIFY VEHICLE'}",
    "{verifyLabel}"
)

if txt == orig:
    print('⚠  No changes made — patterns may already be applied or differ slightly.')
else:
    target.write_text(txt, encoding='utf-8')
    print(f'✅ Fixed {target.name}')
    print()
    print('Verify with:  cd mobile && npm run type-check')
