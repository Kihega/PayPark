#!/usr/bin/env python3
"""
ParkiPay — Replace CI/CD workflows with clean, professional, separate files.

Deletes:
  .github/workflows/ci.yml
  .github/workflows/cd.yml

Creates:
  .github/workflows/backend-ci.yml   — lint + security audit + Jest tests (on develop)
  .github/workflows/backend-cd.yml   — Render deploy (on main, backend/** changes only)
  .github/workflows/mobile-ci.yml    — ESLint + TypeScript check (on develop)
  .github/workflows/mobile-cd.yml    — EAS production build (on main, mobile/** changes only)

Usage:
  python3 patch_workflows.py           # run from repo root
  python3 patch_workflows.py /path/to/PayPark
"""

import sys, shutil
from pathlib import Path

# ── Locate repo root ──────────────────────────────────────────────────────────
REPO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
WF   = REPO / ".github" / "workflows"

if not REPO.is_dir():
    sys.exit(f"ERROR: {REPO} does not exist.")

WF.mkdir(parents=True, exist_ok=True)

applied  = []
removed  = []

def write(name: str, content: str) -> None:
    path = WF / name
    path.write_text(content)
    applied.append(name)
    print(f"  ✓  wrote  .github/workflows/{name}")

def delete(name: str) -> None:
    path = WF / name
    if path.exists():
        path.unlink()
        removed.append(name)
        print(f"  🗑  removed  .github/workflows/{name}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Delete old monolithic workflows
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Removing old workflows ───────────────────────────────────────────────")
delete("ci.yml")
delete("cd.yml")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. backend-ci.yml
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Writing backend-ci.yml ───────────────────────────────────────────────")
write("backend-ci.yml", """\
# =============================================================================
# ParkiPay — Backend CI
#
# Runs on every push / PR that touches backend/** on the develop branch.
# Pipeline:  lint  →  security-audit  →  test  →  merge-to-main
#
# Required secrets  (Settings → Secrets → Actions):
#   GH_PAT   Personal Access Token — scopes: repo, workflow
# =============================================================================

name: Backend CI

on:
  push:
    branches: [develop]
    paths:
      - "backend/**"
      - ".github/workflows/backend-ci.yml"
  pull_request:
    branches: [develop]
    paths:
      - "backend/**"

defaults:
  run:
    working-directory: backend
    shell: bash

# Cancel any in-progress run for the same branch / PR
concurrency:
  group: backend-ci-${{ github.ref }}
  cancel-in-progress: true

jobs:

  # ── Lint ──────────────────────────────────────────────────────────────────
  lint:
    name: Lint (ESLint)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: backend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

  # ── Security Audit ────────────────────────────────────────────────────────
  security-audit:
    name: Security Audit (npm audit)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: backend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Audit for high/critical vulnerabilities
        # Fails the build on high or critical severity CVEs only
        run: npm audit --audit-level=high

  # ── Tests ─────────────────────────────────────────────────────────────────
  test:
    name: Test (Jest + Prisma)
    runs-on: ubuntu-latest
    needs: [lint, security-audit]

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB:       parkipay_test
          POSTGRES_USER:     parkipay
          POSTGRES_PASSWORD: parkipay
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      NODE_ENV:     test
      DATABASE_URL: postgresql://parkipay:parkipay@localhost:5432/parkipay_test
      JWT_SECRET:   ci-test-secret-not-for-production

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: backend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Generate Prisma client
        run: npx prisma generate

      - name: Apply migrations
        run: npx prisma migrate deploy

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: backend-coverage
          path: backend/coverage/
          retention-days: 14

  # ── Merge develop → main (push only, all checks green) ───────────────────
  merge-to-main:
    name: Merge develop → main
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, security-audit, test]

    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_PAT }}

      - name: Configure git identity
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Merge develop into main
        run: |
          git checkout main
          git merge --no-ff develop -m "ci(backend): auto-merge develop → main [skip ci]"
          git push origin main
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. backend-cd.yml
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Writing backend-cd.yml ───────────────────────────────────────────────")
write("backend-cd.yml", """\
# =============================================================================
# ParkiPay — Backend CD
#
# Deploys the Express API to Render whenever backend/** is merged into main.
# Triggered only after CI auto-merge succeeds (see backend-ci.yml).
#
# Required secrets  (Settings → Secrets → Actions):
#   RENDER_DEPLOY_HOOK_URL   Render dashboard → service → Settings → Deploy Hook
# =============================================================================

name: Backend CD

on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/backend-cd.yml"

# One deploy at a time — never queue multiple Render triggers
concurrency:
  group: backend-cd
  cancel-in-progress: false

jobs:

  deploy:
    name: Deploy → Render
    runs-on: ubuntu-latest

    steps:
      - name: Trigger Render deploy hook
        run: |
          HTTP_STATUS=$(
            curl --silent --output /dev/null --write-out "%{http_code}" \
              --max-time 30 \
              -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
          )
          echo "Render responded: HTTP $HTTP_STATUS"
          if [[ "$HTTP_STATUS" -lt 200 || "$HTTP_STATUS" -ge 300 ]]; then
            echo "::error::Render deploy hook failed (HTTP $HTTP_STATUS)"
            exit 1
          fi
          echo "✅ Deploy triggered successfully"

      - name: Annotate commit with deploy info
        run: |
          echo "### 🚀 Backend deployed to Render" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Commit:** \`${{ github.sha }}\`" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Triggered by:** ${{ github.actor }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Time:** $(date -u '+%Y-%m-%d %H:%M UTC')" >> "$GITHUB_STEP_SUMMARY"
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. mobile-ci.yml
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Writing mobile-ci.yml ────────────────────────────────────────────────")
write("mobile-ci.yml", """\
# =============================================================================
# ParkiPay — Mobile CI
#
# Runs on every push / PR that touches mobile/** on the develop branch.
# Pipeline:  lint  →  type-check  →  test  →  merge-to-main
#
# Required secrets  (Settings → Secrets → Actions):
#   GH_PAT   Personal Access Token — scopes: repo, workflow
# =============================================================================

name: Mobile CI

on:
  push:
    branches: [develop]
    paths:
      - "mobile/**"
      - ".github/workflows/mobile-ci.yml"
  pull_request:
    branches: [develop]
    paths:
      - "mobile/**"

defaults:
  run:
    working-directory: mobile
    shell: bash

concurrency:
  group: mobile-ci-${{ github.ref }}
  cancel-in-progress: true

jobs:

  # ── Lint ──────────────────────────────────────────────────────────────────
  lint:
    name: Lint (ESLint)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

  # ── TypeScript ────────────────────────────────────────────────────────────
  type-check:
    name: Type Check (tsc)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: TypeScript strict type check
        run: npm run type-check

  # ── Tests ─────────────────────────────────────────────────────────────────
  test:
    name: Test (Jest)
    runs-on: ubuntu-latest
    needs: [lint, type-check]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --passWithNoTests --coverage

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mobile-coverage
          path: mobile/coverage/
          retention-days: 14

  # ── Merge develop → main (push only, all checks green) ───────────────────
  merge-to-main:
    name: Merge develop → main
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, type-check, test]

    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_PAT }}

      - name: Configure git identity
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Merge develop into main
        run: |
          git checkout main
          git merge --no-ff develop -m "ci(mobile): auto-merge develop → main [skip ci]"
          git push origin main
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. mobile-cd.yml
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Writing mobile-cd.yml ────────────────────────────────────────────────")
write("mobile-cd.yml", """\
# =============================================================================
# ParkiPay — Mobile CD
#
# Triggers an EAS production build for Android + iOS whenever mobile/**
# is merged into main.
#
# Required secrets  (Settings → Secrets → Actions):
#   EXPO_TOKEN   expo.dev → Account Settings → Access Tokens
# =============================================================================

name: Mobile CD

on:
  push:
    branches: [main]
    paths:
      - "mobile/**"
      - ".github/workflows/mobile-cd.yml"

concurrency:
  group: mobile-cd
  cancel-in-progress: false

jobs:

  build:
    name: EAS Build → Production (Android + iOS)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        working-directory: mobile
        run: npm ci

      - name: Install EAS CLI
        run: npm install --global eas-cli

      - name: EAS Build — Android + iOS (production)
        working-directory: mobile
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
        run: |
          eas build \
            --platform all \
            --profile production \
            --non-interactive \
            --no-wait
        # --no-wait: returns immediately; EAS notifies via email + webhook.
        # Remove the flag if you want the workflow to block until the build finishes.

      - name: Annotate commit with build info
        run: |
          echo "### 📱 Mobile EAS build triggered" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Commit:** \`${{ github.sha }}\`" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Triggered by:** ${{ github.actor }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Time:** $(date -u '+%Y-%m-%d %H:%M UTC')" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Check build status:** https://expo.dev" >> "$GITHUB_STEP_SUMMARY"
""")


# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════
print()
if removed:
    print(f"🗑  Removed  : {', '.join(removed)}")
print(f"✅  Created  : {', '.join(applied)}")
print("""
Required GitHub Secrets (Settings → Secrets → Actions):
  GH_PAT                  repo + workflow scopes
  RENDER_DEPLOY_HOOK_URL  Render → service → Settings → Deploy Hook
  EXPO_TOKEN              expo.dev → Account Settings → Access Tokens

Commit:
  git add .github/workflows/
  git commit -m "ci: replace monolithic workflows with separate backend/mobile CI+CD"
  git push origin develop
""")
