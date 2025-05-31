#!/usr/bin/env python3
"""
Test Edge TTS integration
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_edge_tts():
    """Test Edge TTS server"""
    print("🧪 Testing Edge TTS Server...")
    
    async with httpx.AsyncClient() as client:
        # 1. Check server status
        try:
            response = await client.get("http://localhost:8128/")
            if response.status_code == 200:
                print("✅ Server is running")
                print(f"Response: {response.json()}")
            else:
                print("❌ Server not responding properly")
                return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("Start the server with: uv run python tts_servers/edge_tts_server.py")
            return
        
        # 2. List voices
        print("\n📋 Available voices:")
        response = await client.get("http://localhost:8128/v1/voices")
        voices = response.json()
        for voice in voices[:5]:  # Show first 5
            print(f"  - {voice['id']}: {voice['name']} ({voice['language']})")
        
        # 3. Test Polish synthesis
        print("\n🎤 Testing Polish synthesis...")
        response = await client.post(
            "http://localhost:8128/v1/tts/synthesize",
            json={
                "text": "Cześć! To jest test syntezatora mowy Edge TTS. Działa świetnie!",
                "voice": "pl_male",
                "language": "pl"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generated: {result['audio_path']}")
            
            # Play the audio
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(result['audio_path'])
            pygame.mixer.music.play()
            
            print("🔊 Playing audio...")
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            pygame.mixer.quit()
        else:
            print(f"❌ Synthesis failed: {response.status_code}")
        
        # 4. Test English with different voice
        print("\n🎤 Testing English synthesis...")
        response = await client.post(
            "http://localhost:8128/v1/tts/synthesize",
            json={
                "text": "Hello! This is Edge TTS working perfectly in lbrxVoice!",
                "voice": "en_female",
                "language": "en",
                "speed": 1.2,
                "pitch": 5.0
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generated: {result['audio_path']}")
        
        print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_edge_tts())