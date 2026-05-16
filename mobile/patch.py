import re
from pathlib import Path

file = Path("services/api.ts")

text = file.read_text(encoding="utf-8")

# Replace axios import with all required types
text = re.sub(
    r'import\s+.*?\s+from\s+[\'"]axios[\'"];?',
    (
        "import axios, {\n"
        "  AxiosResponse,\n"
        "  AxiosError,\n"
        "  InternalAxiosRequestConfig,\n"
        "} from 'axios';"
    ),
    text,
    flags=re.DOTALL,
)

# Fallback if axios import missing
if "InternalAxiosRequestConfig" not in text:
    text = (
        "import axios, {\n"
        "  AxiosResponse,\n"
        "  AxiosError,\n"
        "  InternalAxiosRequestConfig,\n"
        "} from 'axios';\n\n" + text
    )

file.write_text(text, encoding="utf-8")

print("✓ Fixed axios type imports")
print("Now run: npm run type-check")
