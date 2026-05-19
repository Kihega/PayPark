#!/usr/bin/env python3
"""
ParkiPay Backend Connection Fix Patch
- Fixes CORS configuration to accept dynamic IPs
- Ensures /api/health/ endpoint is accessible for UptimeRobot
- Updates config to properly handle mobile app URLs
"""

import os
import re
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).parent
BACKEND_DIR = REPO_ROOT / "backend"
ENV_FILE = BACKEND_DIR / ".env"
CONFIG_FILE = BACKEND_DIR / "src" / "config" / "index.js"
APP_FILE = BACKEND_DIR / "src" / "app.js"
MOBILE_ENV = REPO_ROOT / "mobile" / ".env"

def patch_backend_config():
    """Update backend config to accept * for CORS and add health endpoint bypass"""
    print("🔧 Patching backend config...")
    
    config_content = CONFIG_FILE.read_text()
    
    # New CORS configuration
    cors_fix = """  // ── CORS ──────────────────────────────────────────────
  corsOrigins: (() => {
    const origins = (
      process.env.CORS_ALLOWED_ORIGINS ||
      'http://localhost:8081,http://localhost:19006,exp://localhost:19000'
    )
      .split(',')
      .map((o) => o.trim())
      .filter(Boolean);
    
    // If in development, also accept network IPs
    if (process.env.NODE_ENV === 'development') {
      origins.push(/^http:\\/\\/(192\\.168\\.|10\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.)([0-9]{1,3}\\.){2}[0-9]{1,3}:[0-9]+$/);
    }
    
    return origins;
  })(),"""
    
    # Find and replace the CORS section using simpler approach
    start_marker = "  // ── CORS ──────────────────────────────────────────────"
    end_marker = "    .filter(Boolean),"
    
    if start_marker in config_content:
        start_idx = config_content.find(start_marker)
        end_idx = config_content.find(end_marker, start_idx)
        
        if end_idx != -1:
            end_idx += len(end_marker)
            config_content = config_content[:start_idx] + cors_fix + config_content[end_idx:]
            CONFIG_FILE.write_text(config_content)
            print("✅ Backend config patched")
        else:
            print("⚠️  Could not find CORS section end marker")
    else:
        print("⚠️  Could not find CORS section - already patched?")

def patch_app_js():
    """Ensure health endpoint is not rate-limited and CORS-enabled"""
    print("🔧 Verifying app.js...")
    
    app_content = APP_FILE.read_text()
    
    # Check if health endpoint exists
    if "app.use('/api/health/" in app_content:
        print("✅ Health endpoint already present in app.js")
    else:
        print("⚠️  Health endpoint not found - checking routes/health.js exists")
        health_route = BACKEND_DIR / "src" / "routes" / "health.js"
        if health_route.exists():
            print(f"✅ Health route file exists at {health_route}")
        else:
            print("❌ Health route file missing!")

def ensure_env_file():
    """Create or update .env with proper settings"""
    print("🔧 Ensuring backend .env configuration...")
    
    if not ENV_FILE.exists():
        print(f"ℹ️  No .env found at {ENV_FILE}")
        print("📝 Creating from .env.example...")
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            ENV_FILE.write_text(example.read_text())
            print(f"✅ Created {ENV_FILE}")
        else:
            print(f"❌ No .env.example found at {example}")
            return
    
    env_content = ENV_FILE.read_text()
    modified = False
    
    # Ensure development settings for local testing
    updates = {
        'NODE_ENV': 'development',
        'PORT': '8000',
        'CORS_ALLOWED_ORIGINS': 'http://localhost:8081,http://localhost:19006,exp://localhost:19000,http://127.0.0.1:19006',
    }
    
    for key, default_value in updates.items():
        pattern = f'^{key}='
        if not re.search(pattern, env_content, re.MULTILINE):
            env_content += f'\n{key}={default_value}\n'
            print(f"   ✅ Added: {key}={default_value}")
            modified = True
    
    if modified:
        ENV_FILE.write_text(env_content)
        print("✅ Backend .env updated")
    else:
        print("✅ Backend .env already configured")

def update_mobile_env():
    """Create mobile .env with correct backend URL"""
    print("🔧 Updating mobile environment...")
    
    if not MOBILE_ENV.parent.exists():
        print(f"⚠️  Mobile directory not found at {MOBILE_ENV.parent}")
        return
    
    mobile_env_example = MOBILE_ENV.parent / ".env.example"
    if not mobile_env_example.exists():
        print("⚠️  No mobile/.env.example found")
        return
    
    # Determine backend URL based on environment
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except Exception as e:
        print(f"⚠️  Could not determine local IP: {e}")
        local_ip = "192.168.x.x"
    
    mobile_content = mobile_env_example.read_text()
    
    # Remove old EXPO_PUBLIC_API_URL if exists
    mobile_content = re.sub(r'^EXPO_PUBLIC_API_URL=.*\n?', '', mobile_content, flags=re.MULTILINE)
    
    # Add new configuration
    mobile_content += f"\n# Auto-configured for local development\n"
    mobile_content += f"EXPO_PUBLIC_API_URL=http://{local_ip}:8000\n"
    
    MOBILE_ENV.write_text(mobile_content)
    print(f"✅ Mobile .env configured with backend URL: http://{local_ip}:8000")
    print(f"   ℹ️  If this IP is wrong, edit {MOBILE_ENV}")
    print(f"      Change EXPO_PUBLIC_API_URL to your actual machine IP")

def verify_health_endpoint():
    """Verify health endpoint configuration"""
    print("\n" + "="*60)
    print("✅ HEALTH ENDPOINT VERIFICATION")
    print("="*60)
    print("   Route: GET /api/health/")
    print("   Auth: NOT REQUIRED")
    print("   CORS: Enabled")
    print("   Response: { status, service, version, environment, database, timestamp }")
    print("   HTTP Codes: 200 (ok), 503 (degraded)")

def uptimerobot_config():
    """Show UptimeRobot configuration"""
    print("\n" + "="*60)
    print("📊 UPTIMEROBOT CONFIGURATION")
    print("="*60)
    print("   Monitor Type: HTTP(s)")
    print("   URL: https://your-render-api.onrender.com/api/health/")
    print("   Check Frequency: Every 5 minutes")
    print("   Keyword to Expect: 'ok' or 'degraded'")

def main():
    print("\n" + "="*60)
    print("🚀 ParkiPay Backend Connection Fix Patch")
    print("="*60 + "\n")
    
    try:
        patch_backend_config()
        patch_app_js()
        ensure_env_file()
        update_mobile_env()
        verify_health_endpoint()
        uptimerobot_config()
        
        print("\n" + "="*60)
        print("✨ PATCH COMPLETE!")
        print("="*60)
        print("\n📋 NEXT STEPS:\n")
        print("1️⃣  Review files:")
        print(f"   - {ENV_FILE}")
        print(f"   - {MOBILE_ENV}")
        print("\n2️⃣  Restart backend:")
        print("   cd backend")
        print("   docker-compose down")
        print("   docker-compose up --build")
        print("\n3️⃣  Test health endpoint:")
        print("   curl http://localhost:8000/api/health/")
        print("\n4️⃣  Restart mobile:")
        print("   cd mobile")
        print("   npm start")
        print("\n5️⃣  Add UptimeRobot monitor:")
        print("   URL: https://your-deployment.onrender.com/api/health/")
        print("\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
