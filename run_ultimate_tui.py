#!/usr/bin/env python3
"""
Launch script for lbrxChat Ultimate
Starts all required servers and the TUI interface
"""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

# Add to Python path
sys.path.insert(0, str(Path(__file__).parent))


def check_servers():
    """Check if required servers are running"""
    import httpx
    
    servers = {
        "Whisper Batch": "http://localhost:8123/health",
        "Whisper Realtime": "http://localhost:8126/health",
        "TTS DIA": "http://localhost:8124/health",
        "TTS CSM": "http://localhost:8125/health",
        "LM Studio": "http://localhost:1234/v1/models"
    }
    
    client = httpx.Client(timeout=2.0)
    status = {}
    
    for name, url in servers.items():
        try:
            if "localhost:1234" in url:
                # LM Studio check
                response = client.get(url)
                status[name] = response.status_code == 200
            else:
                # Our servers
                response = client.get(url)
                status[name] = response.status_code == 200
        except:
            status[name] = False
    
    return status


def print_server_status(status):
    """Print server status"""
    print("\n🔍 Server Status:")
    print("-" * 40)
    
    for name, is_running in status.items():
        icon = "✅" if is_running else "❌"
        print(f"{icon} {name}: {'Running' if is_running else 'Not running'}")
    
    print("-" * 40)


def start_servers():
    """Start required servers"""
    print("\n🚀 Starting servers...")
    
    # Start Whisper servers
    print("Starting Whisper servers...")
    subprocess.Popen(
        [sys.executable, "start_servers.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for servers to start
    time.sleep(5)
    
    print("Servers should be starting up...")


def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════╗
    ║     lbrxChat Ultimate Launcher        ║
    ║   6-Tab Audio/Voice/AI Platform      ║
    ║           (c)2025 M&K                 ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Check server status
    status = check_servers()
    print_server_status(status)
    
    # Check if we need to start servers
    all_running = all([
        status.get("Whisper Batch", False),
        status.get("Whisper Realtime", False),
        # TTS servers are optional
        # LM Studio should be started manually
    ])
    
    if not all_running:
        print("\n⚠️  Some required servers are not running.")
        
        response = input("\nStart missing servers? (y/n): ")
        if response.lower() == 'y':
            start_servers()
            
            # Re-check status
            print("\nWaiting for servers to initialize...")
            time.sleep(5)
            status = check_servers()
            print_server_status(status)
    
    # Check LM Studio specifically
    if not status.get("LM Studio", False):
        print("\n⚠️  LM Studio is not running!")
        print("Please start LM Studio and load a model (e.g., qwen3-8b)")
        print("The chat features will not work without it.")
        
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Launch TUI
    print("\n🎯 Launching lbrxChat Ultimate TUI...")
    print("Press Ctrl+C to exit\n")
    
    try:
        from lbrxchat.lbrx_ultimate_tui import main as run_tui
        run_tui()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except ImportError as e:
        print(f"\n❌ Error importing TUI: {e}")
        print("Make sure all dependencies are installed:")
        print("  uv pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()