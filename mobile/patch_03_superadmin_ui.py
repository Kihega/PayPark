#!/usr/bin/env python3
"""ParkiPay — Fix TS2304: remove orphaned `slideX = useRef_anim(...)` line in admin.tsx"""
import sys
from pathlib import Path

def find_root(arg=None):
    if arg: return Path(arg).resolve()
    for base in [Path.cwd(), Path('/home/kali'), Path('/home/kali/PayPark')]:
        for suf in ['', 'PayPark-main']:
            p = base / suf
            if (p / 'backend' / 'prisma' / 'schema.prisma').exists(): return p
    sys.exit('Pass path: python3 paypark_lintfix4.py /home/kali/PayPark')

root = find_root(sys.argv[1] if len(sys.argv) > 1 else None)
f    = root / 'mobile' / 'app' / '(app)' / 'admin.tsx'
txt  = f.read_text(encoding='utf-8')

LINE = "  const slideX = useRef_anim(new Animated.Value(-SIDEBAR_W));\n"

if LINE in txt:
    f.write_text(txt.replace(LINE, '', 1), encoding='utf-8')
    print('✅ Removed orphaned slideX line from admin.tsx')
else:
    print('⚠  Line not found — may already be removed.')

print('Run: cd mobile && npm run type-check && npm run lint')
