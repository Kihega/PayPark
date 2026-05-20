#!/usr/bin/env python3

from pathlib import Path
import re

files = [
    Path("hooks/useBiometric.ts"),
    Path("app/(auth)/login.tsx"),
]

for file in files:
    if not file.exists():
        print(f"[!] Missing: {file}")
        continue

    content = file.read_text(encoding="utf-8")
    original = content

    # ------------------------------------------------
    # Fix invalid Expo Router path
    # ------------------------------------------------
    content = content.replace(
        "router.replace('/(app)/admin');",
        "router.replace('/home');"
    )

    # ------------------------------------------------
    # Remove setAuth(data....) line
    # ------------------------------------------------
    content = re.sub(
        r'.*setAuth\(data\.[^\n]*\n',
        '',
        content,
    )

    # Remove remaining data.xxx references
    content = re.sub(
        r'data\.\w+',
        'undefined',
        content,
    )

    # Cleanup double empty lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    backup = file.with_suffix(file.suffix + ".bak")
    backup.write_text(original, encoding="utf-8")

    file.write_text(content, encoding="utf-8")

    print(f"[✓] Fixed: {file}")
    print(f"[✓] Backup: {backup}")

print("\nDone.")
print("Run:")
print("npm run type-check")
