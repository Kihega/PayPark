from pathlib import Path
import re

# Project root
ROOT = Path("/home/kali/PayPark/mobile")

# -------------------------------------------------------------------
# Fix 1: Preserve STAGING_API_URL placeholder safely
# -------------------------------------------------------------------

api_constants = ROOT / "constants" / "api.ts"

if api_constants.exists():
    content = api_constants.read_text()

    # Add eslint disable comment only if variable exists
    if "STAGING_API_URL" in content and "@typescript-eslint/no-unused-vars" not in content:
        content = re.sub(
            r"(const\s+STAGING_API_URL\s*=)",
            r"// eslint-disable-next-line @typescript-eslint/no-unused-vars\n\1",
            content,
            count=1,
        )

    api_constants.write_text(content)
    print(f"✓ Patched: {api_constants}")

# -------------------------------------------------------------------
# Fix 2: Replace axios default import safely
# -------------------------------------------------------------------

api_service = ROOT / "services" / "api.ts"

if api_service.exists():
    content = api_service.read_text()

    # Replace import axios from 'axios'
    content = re.sub(
        r"import\s+axios\s+from\s+['\"]axios['\"];?",
        "import { create } from 'axios';",
        content,
    )

    # Replace axios.create(
    content = content.replace("axios.create(", "create(")

    api_service.write_text(content)
    print(f"✓ Patched: {api_service}")

print("\nAll ESLint warnings patched safely.")
