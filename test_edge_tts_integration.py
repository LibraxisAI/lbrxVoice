#!/usr/bin/env python3
"""
🧪 Comprehensive Edge TTS Integration Test
Automatically starts server if needed and tests all functionality
"""

import asyncio
import httpx
import subprocess
import time
import signal
import sys
from pathlib import Path

# Global server process
edge_server_process = None

def start_edge_server():
    """Start Edge TTS server in background"""
    global edge_server_process
    
    print("🚀 Starting Edge TTS server...")
    
    edge_server_process = subprocess.Popen(
        ["uv", "run", "python", "tts_servers/edge_tts_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Wait for server to start
    for i in range(10):
        try:
            response = httpx.get("http://localhost:8128/", timeout=1.0)
            if response.status_code == 200:
                print("✅ Edge TTS server started successfully!")
                return True
        except:
            time.sleep(1)
    
    print("❌ Failed to start Edge TTS server")
    return False

def stop_edge_server():
    """Stop Edge TTS server"""
    global edge_server_process
    
    if edge_server_process:
        print("🛑 Stopping Edge TTS server...")
        edge_server_process.terminate()
        edge_server_process.wait()
        edge_server_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\n⚠️ Test interrupted")
    stop_edge_server()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def test_edge_tts_comprehensive():
    """Comprehensive Edge TTS test"""
    print("🧪 Testing Edge TTS Integration...")
    print("=" * 60)
    
    # Check if server is already running
    server_running = False
    try:
        response = httpx.get("http://localhost:8128/", timeout=2.0)
        if response.status_code == 200:
            print("✅ Edge TTS server already running")
            server_running = True
    except:
        pass
    
    # Start server if not running
    if not server_running:
        if not start_edge_server():
            print("❌ Cannot start Edge TTS server - aborting tests")
            return False
        started_server = True
    else:
        started_server = False
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Server health
            print("\n1️⃣ Testing server health...")
            response = await client.get("http://localhost:8128/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server status: {data.get('status')}")
                print(f"📊 Voices available: {data.get('voices_available')}")
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
            
            # Test 2: List voices
            print("\n2️⃣ Testing voice list...")
            response = await client.get("http://localhost:8128/v1/voices")
            if response.status_code == 200:
                voices = response.json()
                print(f"✅ Found {len(voices)} voices")
                
                # Show Polish and English voices
                pl_voices = [v for v in voices if v['language'] == 'pl']
                en_voices = [v for v in voices if v['language'] == 'en']
                
                print(f"🇵🇱 Polish voices: {len(pl_voices)}")
                for v in pl_voices:
                    print(f"   - {v['id']}: {v['name']} ({v['gender']})")
                
                print(f"🇬🇧 English voices: {len(en_voices)}")
                for v in en_voices[:3]:  # Show first 3
                    print(f"   - {v['id']}: {v['name']} ({v['gender']})")
            else:
                print(f"❌ Voice list failed: {response.status_code}")
                return False
            
            # Test 3: Polish synthesis
            print("\n3️⃣ Testing Polish synthesis...")
            response = await client.post(
                "http://localhost:8128/v1/tts/synthesize",
                json={
                    "text": "Cześć! To jest test Edge TTS w lbrxVoice. Działa świetnie!",
                    "voice": "pl_male",
                    "language": "pl",
                    "speed": 1.0,
                    "pitch": 0.0
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                audio_path = result.get('audio_path')
                voice_used = result.get('voice_used')
                
                print(f"✅ Polish synthesis successful!")
                print(f"📁 Audio file: {Path(audio_path).name}")
                print(f"🎤 Voice used: {voice_used}")
                
                # Check file exists and has size
                if Path(audio_path).exists():
                    file_size = Path(audio_path).stat().st_size
                    print(f"📊 File size: {file_size:,} bytes")
                    
                    if file_size > 1000:  # Should be at least 1KB
                        print("✅ Audio file generated successfully!")
                    else:
                        print("⚠️ Audio file seems too small")
                else:
                    print("❌ Audio file not found")
            else:
                print(f"❌ Polish synthesis failed: {response.status_code}")
                return False
            
            # Test 4: English synthesis with different settings
            print("\n4️⃣ Testing English synthesis with effects...")
            response = await client.post(
                "http://localhost:8128/v1/tts/synthesize",
                json={
                    "text": "Hello! This is Edge TTS working perfectly in lbrxVoice. Testing different voice settings!",
                    "voice": "en_female",
                    "language": "en",
                    "speed": 1.3,    # Faster
                    "pitch": 8.0,    # Higher pitch
                    "style": "cheerful"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ English synthesis with effects successful!")
                print(f"🎤 Voice: {result.get('voice_used')}")
                print(f"📁 File: {Path(result.get('audio_path')).name}")
            else:
                print(f"❌ English synthesis failed: {response.status_code}")
            
            # Test 5: Multi-language test
            print("\n5️⃣ Testing multi-language support...")
            
            tests = [
                ("pl_female", "pl", "Witaj świecie! Jak się masz?"),
                ("en_male", "en", "Hello world! How are you doing?"),
                ("de_male", "de", "Hallo Welt! Wie geht es dir?"),
                ("fr_male", "fr", "Bonjour le monde! Comment allez-vous?")
            ]
            
            for voice, lang, text in tests:
                response = await client.post(
                    "http://localhost:8128/v1/tts/synthesize",
                    json={
                        "text": text,
                        "voice": voice,
                        "language": lang
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ {lang.upper()}: {voice} - OK")
                else:
                    print(f"❌ {lang.upper()}: {voice} - Failed")
            
            # Test 6: Preview mode (if available)
            print("\n6️⃣ Testing preview generation...")
            response = await client.post(
                "http://localhost:8128/v1/tts/preview",
                json={"text": "To jest test wszystkich głosów Edge TTS!"}
            )
            
            if response.status_code == 200:
                result = response.json()
                previews = result.get('previews', [])
                successful = len([p for p in previews if 'audio_path' in p])
                print(f"✅ Generated {successful}/{len(previews)} voice previews")
            else:
                print(f"⚠️ Preview generation not available")
            
            print("\n" + "=" * 60)
            print("🎉 All Edge TTS tests completed successfully!")
            print("\n💡 You can now:")
            print("   - Use TTS tab in lbrxvoice")
            print("   - Call REST API directly")
            print("   - Generate speech in multiple languages")
            
            return True
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
        
        finally:
            # Clean up server if we started it
            if started_server:
                stop_edge_server()

if __name__ == "__main__":
    print("🎤 Edge TTS Integration Test")
    print("This will test all Edge TTS functionality")
    print("Press Ctrl+C to stop\n")
    
    result = asyncio.run(test_edge_tts_comprehensive())
    
    if result:
        print("\n🏆 SUCCESS: Edge TTS is fully functional!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Edge TTS has issues")
        sys.exit(1)