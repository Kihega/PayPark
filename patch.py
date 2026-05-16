import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND = BASE_DIR / "backend"

def run(cmd, cwd=None):
    print(f"\n▶ {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR)

def enforce_nvm_node():
    print("\n=== Enforcing Node via NVM ===")

    version = subprocess.getoutput("node -v")

    if "v20" in version or "v21" in version or "v22" in version:
        print(f"✔ Node OK: {version}")
        return

    print(f"❌ Current Node: {version}")
    print("👉 Switching to Node 20 via NVM...")

    run("nvm install 20")
    run("nvm use 20")
    run("nvm alias default 20")

def fix_backend():
    print("\n=== Backend Fix ===")

    shutil.rmtree(BACKEND / "node_modules", ignore_errors=True)

    run("npm ci", cwd=BACKEND)

    if (BACKEND / "prisma").exists():
        run("npx prisma generate", cwd=BACKEND)

    print("✔ Backend fixed")

def main():
    print("\n🚀 PayPark NVM Patch Starting...\n")

    enforce_nvm_node()
    fix_backend()

    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
