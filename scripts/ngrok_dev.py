#!/usr/bin/env python3
"""
ngrok Local Development Setup
==============================
Exposes the FastAPI backend via ngrok for:
  - Webhook testing (receive events on public URL)
  - Microsoft Graph OAuth callback testing
  - Mobile/external testing

Usage:
    pip install pyngrok
    NGROK_AUTH_TOKEN=your_token python scripts/ngrok_dev.py
"""
import os
import sys
import asyncio
import subprocess
from pyngrok import ngrok, conf

AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))


def setup_ngrok():
    if not AUTH_TOKEN:
        print("⚠️  NGROK_AUTH_TOKEN not set — running in unauthenticated mode (limited)")
    else:
        conf.get_default().auth_token = AUTH_TOKEN

    # Open tunnels
    backend_tunnel = ngrok.connect(BACKEND_PORT, "http", subdomain=None)
    frontend_tunnel = ngrok.connect(FRONTEND_PORT, "http", subdomain=None)

    backend_url = backend_tunnel.public_url
    frontend_url = frontend_tunnel.public_url

    print("\n" + "="*60)
    print("🚀 ngrok tunnels active:")
    print(f"   Backend  (API):    {backend_url}")
    print(f"   Frontend (UI):     {frontend_url}")
    print(f"   Swagger docs:      {backend_url}/api/v1/docs")
    print("="*60)
    print("\n📋 For webhook testing:")
    print(f"   Register endpoint: {backend_url}/api/v1/webhooks/receive")
    print("\n📋 For Azure OAuth callback:")
    print(f"   Redirect URI:      {backend_url}/api/v1/auth/callback")
    print("\n📋 Update your .env:")
    print(f"   NGROK_PUBLIC_URL={backend_url}")
    print(f"   FRONTEND_URL={frontend_url}")
    print("\nPress Ctrl+C to stop...\n")

    # Write public URL to .env for the backend to use
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    _update_env(env_path, 'NGROK_PUBLIC_URL', backend_url)

    try:
        ngrok.get_ngrok_process().proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ngrok tunnels...")
        ngrok.kill()


def _update_env(path: str, key: str, value: str):
    """Update or append a key in a .env file."""
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break

    if not found:
        lines.append(f"{key}={value}\n")

    with open(path, 'w') as f:
        f.writelines(lines)


if __name__ == "__main__":
    setup_ngrok()
