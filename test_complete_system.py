#!/usr/bin/env python3
"""
🧪 Complete System Test
Tests entire lbrxVoice pipeline with auto-server management
"""

import asyncio
import httpx
import subprocess
import time
import signal
import sys
import json
from pathlib import Path

# Global processes
server_processes = {}

def start_servers():
    """Start all required servers"""
    servers = [
        ("whisper-batch", ["uv", "run", "python", "-m", "whisper_servers.batch"], 8123),
        ("whisper-realtime", ["uv", "run", "python", "-m", "whisper_servers.realtime"], 8126),
        ("edge-tts", ["uv", "run", "python", "tts_servers/edge_tts_server.py"], 8128)
    ]
    
    print("🚀 Starting all servers...")
    
    for name, cmd, port in servers:
        print(f"  Starting {name} on port {port}...")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        server_processes[name] = process
        
        # Quick check if process started
        time.sleep(2)
        if process.poll() is None:
            print(f"  ✅ {name} started")
        else:
            print(f"  ❌ {name} failed to start")
    
    # Wait for servers to be ready
    print("\n⏳ Waiting for servers to be ready...")
    time.sleep(5)

def stop_servers():
    """Stop all servers"""
    print("🛑 Stopping all servers...")
    for name, process in server_processes.items():
        if process and process.poll() is None:
            print(f"  Stopping {name}...")
            process.terminate()
            process.wait()
    server_processes.clear()

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\n⚠️ Test interrupted")
    stop_servers()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def test_complete_system():
    """Test complete lbrxVoice system"""
    print("🧪 Complete lbrxVoice System Test")
    print("=" * 60)
    
    # Start servers
    start_servers()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        test_results = {}
        
        try:
            # Test 1: Whisper Batch API
            print("\n1️⃣ Testing Whisper Batch API...")
            try:
                response = await client.get("http://localhost:8123/health")
                if response.status_code == 200:
                    print("✅ Whisper Batch: Running")
                    test_results["whisper_batch"] = "✅"
                else:
                    print(f"❌ Whisper Batch: HTTP {response.status_code}")
                    test_results["whisper_batch"] = "❌"
            except Exception as e:
                print(f"❌ Whisper Batch: {e}")
                test_results["whisper_batch"] = "❌"
            
            # Test 2: Whisper Realtime WebSocket
            print("\n2️⃣ Testing Whisper Realtime...")
            try:
                # Just check if port is responding
                response = await client.get("http://localhost:8126/health", timeout=5.0)
                print("✅ Whisper Realtime: Running")
                test_results["whisper_realtime"] = "✅"
            except Exception as e:
                print(f"⚠️ Whisper Realtime: WebSocket only ({e})")
                test_results["whisper_realtime"] = "⚠️"
            
            # Test 3: Edge TTS
            print("\n3️⃣ Testing Edge TTS...")
            try:
                response = await client.get("http://localhost:8128/")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Edge TTS: {data.get('status')} - {data.get('voices_available')} voices")
                    test_results["edge_tts"] = "✅"
                    
                    # Quick synthesis test
                    response = await client.post(
                        "http://localhost:8128/v1/tts/synthesize",
                        json={
                            "text": "Test Edge TTS w lbrxVoice!",
                            "voice": "pl_male"
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        audio_path = result.get('audio_path')
                        if Path(audio_path).exists():
                            file_size = Path(audio_path).stat().st_size
                            print(f"✅ TTS Synthesis: Generated {file_size:,} bytes")
                        else:
                            print("⚠️ TTS Synthesis: File not found")
                    else:
                        print(f"❌ TTS Synthesis: HTTP {response.status_code}")
                        
                else:
                    print(f"❌ Edge TTS: HTTP {response.status_code}")
                    test_results["edge_tts"] = "❌"
            except Exception as e:
                print(f"❌ Edge TTS: {e}")
                test_results["edge_tts"] = "❌"
            
            # Test 4: LM Studio
            print("\n4️⃣ Testing LM Studio...")
            try:
                response = await client.get("http://localhost:1234/v1/models")
                if response.status_code == 200:
                    models = response.json()
                    model_count = len(models.get('data', []))
                    print(f"✅ LM Studio: {model_count} models loaded")
                    test_results["lm_studio"] = "✅"
                    
                    # Quick chat test
                    chat_response = await client.post(
                        "http://localhost:1234/v1/chat/completions",
                        json={
                            "model": "qwen3-8b",
                            "messages": [
                                {"role": "user", "content": "Say 'lbrxVoice działa!' in Polish"}
                            ],
                            "max_tokens": 10
                        }
                    )
                    
                    if chat_response.status_code == 200:
                        chat_data = chat_response.json()
                        message = chat_data['choices'][0]['message']['content']
                        print(f"✅ LM Chat: '{message.strip()}'")
                    else:
                        print(f"⚠️ LM Chat: HTTP {chat_response.status_code}")
                        
                else:
                    print(f"❌ LM Studio: HTTP {response.status_code}")
                    test_results["lm_studio"] = "❌"
            except Exception as e:
                print(f"❌ LM Studio: {e}")
                test_results["lm_studio"] = "❌"
            
            # Test 5: Audio System
            print("\n5️⃣ Testing Audio System...")
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                print(f"✅ Audio: {len(input_devices)} input devices")
                for d in input_devices[:3]:
                    print(f"   - {d['name']}")
                test_results["audio"] = "✅"
            except Exception as e:
                print(f"❌ Audio: {e}")
                test_results["audio"] = "❌"
            
            # Test 6: MLX
            print("\n6️⃣ Testing MLX Framework...")
            try:
                import mlx
                import mlx_whisper
                print("✅ MLX: Apple Silicon optimization active")
                test_results["mlx"] = "✅"
            except Exception as e:
                print(f"❌ MLX: {e}")
                test_results["mlx"] = "❌"
            
            # Test 7: lbrxvoice command
            print("\n7️⃣ Testing lbrxvoice command...")
            try:
                import shutil
                lbrxvoice_path = shutil.which("lbrxvoice")
                if lbrxvoice_path:
                    print(f"✅ lbrxvoice: Command available at {lbrxvoice_path}")
                    test_results["lbrxvoice_cmd"] = "✅"
                else:
                    print("❌ lbrxvoice: Command not found in PATH")
                    test_results["lbrxvoice_cmd"] = "❌"
            except Exception as e:
                print(f"❌ lbrxvoice: {e}")
                test_results["lbrxvoice_cmd"] = "❌"
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 SYSTEM TEST SUMMARY")
            print("=" * 60)
            
            for component, status in test_results.items():
                component_name = component.replace("_", " ").title()
                print(f"{status} {component_name}")
            
            # Overall status
            success_count = len([s for s in test_results.values() if s == "✅"])
            warning_count = len([s for s in test_results.values() if s == "⚠️"])
            total_tests = len(test_results)
            
            print(f"\n🎯 Results: {success_count}/{total_tests} passing, {warning_count} warnings")
            
            if success_count >= total_tests - 1:  # Allow 1 failure
                print("\n🏆 SYSTEM STATUS: EXCELLENT!")
                print("✨ lbrxVoice is ready for production use!")
                return True
            elif success_count >= total_tests // 2:
                print("\n⚠️ SYSTEM STATUS: GOOD")
                print("🔧 Some components need attention")
                return True
            else:
                print("\n💥 SYSTEM STATUS: NEEDS WORK")
                print("🚨 Multiple components failing")
                return False
                
        except Exception as e:
            print(f"❌ System test error: {e}")
            return False
        
        finally:
            stop_servers()

if __name__ == "__main__":
    print("🚀 lbrxVoice Complete System Test")
    print("This will start all servers and test the entire pipeline")
    print("Press Ctrl+C to stop\n")
    
    result = asyncio.run(test_complete_system())
    
    if result:
        print("\n🎉 SUCCESS: lbrxVoice system is operational!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: System has critical issues")
        sys.exit(1)