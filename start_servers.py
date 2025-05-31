#!/usr/bin/env python3
"""
Start all servers for TTS pipeline testing
"""

import subprocess
import time
import sys
import signal
import os
from pathlib import Path

processes = []

def signal_handler(sig, frame):
    print("\n\nShutting down servers...")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_server(name, command, port, extra_env=None):
    """Start a server in background"""
    print(f"Starting {name} on port {port}...")
    
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    if extra_env:
        env.update(extra_env)
    
    # Prepend uv run to command
    if not command.startswith("uv run"):
        command = f"uv run {command}"
    
    log_file = open(f"logs/{name}.log", "w")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env
    )
    processes.append(process)
    return process

def main():
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    print("🚀 Starting all servers for TTS pipeline...\n")
    
    # Set environment variables for custom ports
    env = os.environ.copy()
    env['REALTIME_PORT'] = '8126'  # Override default realtime port
    env['DIA_WS_PORT'] = '8129'
    env['DIA_REST_PORT'] = '8132'
    env['CSM_REST_PORT'] = '8135'
    
    # Start Whisper servers
    start_server("whisper-batch", "python -m whisper_servers batch", 8123)
    time.sleep(3)
    
    start_server("whisper-realtime", "python -m whisper_servers realtime", 8126, {"REALTIME_PORT": "8126"})
    time.sleep(3)
    
    # Start Edge TTS server (działa!)
    start_server("edge-tts", "python tts_servers/edge_tts_server.py", 8128)
    time.sleep(3)
    
    # Start XTTS server (commented out - not working)
    # start_server("xtts-rest", "python tts_servers/xtts_rest_api.py", 8127)
    # time.sleep(3)
    
    # Other TTS servers (commented out for now - need to fix first)
    # start_server("dia-ws", f"DIA_WS_PORT=8129 python -m tts_servers dia-ws", 8129)
    # time.sleep(3)
    
    # start_server("dia-rest", f"DIA_REST_PORT=8132 python -m tts_servers dia-rest", 8132)
    # time.sleep(3)
    
    # start_server("csm-rest", f"CSM_REST_PORT=8135 python -m tts_servers csm-rest", 8135)
    
    print("\n✅ Servers started:")
    print("  - Whisper Batch: http://localhost:8123")
    print("  - Whisper Realtime: ws://localhost:8126")
    print("  - Edge TTS: http://localhost:8128")
    # print("  - XTTS REST: http://localhost:8127")
    # print("  - DIA WebSocket: ws://localhost:8129")
    # print("  - DIA REST: http://localhost:8132")
    # print("  - CSM REST: http://localhost:8135")
    
    print("\n📊 Logs available in ./logs/")
    print("\nPress Ctrl+C to stop all servers")
    
    # Keep running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()