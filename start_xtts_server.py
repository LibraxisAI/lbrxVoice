#!/usr/bin/env python3
"""
Start XTTS MLX server for Polish TTS
"""

import subprocess
import sys
import time
from pathlib import Path

def start_server():
    """Start XTTS server"""
    print("🎤 Starting XTTS MLX Server...")
    print("   Polish language support enabled")
    print("   Running on http://localhost:8127")
    print("-" * 40)
    
    # Start server
    server_path = Path(__file__).parent / "tts_servers" / "xtts_mlx.py"
    
    try:
        # Run the server
        subprocess.run([sys.executable, str(server_path)])
    except KeyboardInterrupt:
        print("\n\n👋 XTTS server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    start_server()