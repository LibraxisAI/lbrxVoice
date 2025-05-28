#!/usr/bin/env python3
"""
Start all servers for testing
"""

import subprocess
import time
import os
import signal
import sys

class ServerManager:
    def __init__(self):
        self.processes = []
        
    def start_server(self, name, command, port):
        """Start a server process"""
        print(f"\n🚀 Starting {name} on port {port}...")
        
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            command,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if sys.platform != 'win32' else None
        )
        
        self.processes.append((name, process, port))
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {name} started successfully")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {name} failed to start")
            print(f"Error: {stderr}")
            return False
            
    def stop_all(self):
        """Stop all server processes"""
        print("\n🛑 Stopping all servers...")
        
        for name, process, port in self.processes:
            if process.poll() is None:
                if sys.platform != 'win32':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait()
                print(f"✅ Stopped {name}")
                
    def run_test_servers(self):
        """Start servers needed for testing"""
        
        servers = [
            ("Whisper Batch", "whisper-batch-server", 8123),
            ("CSM REST", "python -m tts_servers csm-rest", 8126),
        ]
        
        try:
            for name, cmd, port in servers:
                if not self.start_server(name, cmd, port):
                    print(f"\n❌ Failed to start {name}. Stopping all servers.")
                    self.stop_all()
                    return False
                    
            print("\n✅ All servers started successfully!")
            print("\nServers running:")
            print("- Whisper Batch: http://localhost:8123")
            print("- CSM REST: http://localhost:8126")
            print("\nPress Ctrl+C to stop all servers")
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal")
            self.stop_all()
            
    def test_individual_imports(self):
        """Test if modules can be imported"""
        print("\n🧪 Testing module imports...")
        
        tests = [
            ("Whisper servers", "import whisper_servers"),
            ("TTS servers", "import tts_servers"),
            ("CSM module", "from tts_servers.csm import rest_api"),
        ]
        
        for name, import_cmd in tests:
            try:
                exec(import_cmd)
                print(f"✅ {name} - OK")
            except Exception as e:
                print(f"❌ {name} - Error: {e}")
                

def main():
    manager = ServerManager()
    
    # First test imports
    manager.test_individual_imports()
    
    # Ask user what to do
    print("\n📋 Options:")
    print("1. Start test servers (Whisper + CSM)")
    print("2. Test imports only")
    print("3. Exit")
    
    choice = input("\nChoice: ")
    
    if choice == "1":
        manager.run_test_servers()
    elif choice == "2":
        print("Import tests completed.")
    else:
        print("Exiting.")
        

if __name__ == "__main__":
    main()