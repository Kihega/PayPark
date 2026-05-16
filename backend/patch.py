from pathlib import Path
import re

FILES = [
    "apps/billing/urls.py",
    "apps/vehicles/urls.py",
    "core/exceptions.py",
]

def remove_import(file_path, pattern):
    text = file_path.read_text(encoding="utf-8")
    new_text = re.sub(pattern, "", text, flags=re.MULTILINE)
    file_path.write_text(new_text, encoding="utf-8")

# ----------------------------
# 1. Django urls.py cleanup
# ----------------------------
for path in [
    Path("apps/billing/urls.py"),
    Path("apps/vehicles/urls.py"),
]:
    if path.exists():
        text = path.read_text(encoding="utf-8")

        # remove: from django.urls import path
        text = re.sub(r"^\s*from\s+django\.urls\s+import\s+path\s*\n", "", text, flags=re.MULTILINE)

        path.write_text(text, encoding="utf-8")
        print(f"✓ cleaned {path}")

# ----------------------------
# 2. DRF exceptions cleanup
# ----------------------------
exc = Path("core/exceptions.py")

if exc.exists():
    text = exc.read_text(encoding="utf-8")

    # remove unused imports
    text = re.sub(r"^\s*from\s+rest_framework\.response\s+import\s+Response\s*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*from\s+rest_framework\s+import\s+status\s*\n", "", text, flags=re.MULTILINE)

    exc.write_text(text, encoding="utf-8")
    print(f"✓ cleaned {exc}")

print("\nDone. Run: flake8 . --max-line-length=120 --exclude=migrations,__pycache__,.venv")
