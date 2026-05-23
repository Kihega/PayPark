#!/usr/bin/env python3
"""ParkiPay — Lint fix 2: remove unused `officer` in admin.tsx line 25"""
import sys
from pathlib import Path

def find_root(arg=None):
    if arg: return Path(arg).resolve()
    for base in [Path.cwd(), Path('/home/kali'), Path('/home/kali/PayPark')]:
        for suf in ['', 'PayPark-main']:
            p = base / suf
            if (p / 'backend' / 'prisma' / 'schema.prisma').exists(): return p
    sys.exit('Pass path: python3 paypark_lintfix2.py /home/kali/PayPark')

root  = find_root(sys.argv[1] if len(sys.argv) > 1 else None)
f     = root / 'mobile' / 'app' / '(app)' / 'admin.tsx'
txt   = f.read_text(encoding='utf-8')
fixed = txt.replace(
    "  const { clearAuth, refreshToken, officer } = useAuthStore();",
    "  const { clearAuth, refreshToken } = useAuthStore();"
)
if fixed == txt:
    print('⚠  Pattern not found — may already be fixed.')
else:
    f.write_text(fixed, encoding='utf-8')
    print('✅ Fixed — removed unused `officer` from admin.tsx')
print('Run: cd mobile && npm run lint')
