#!/usr/bin/env python3
"""Test XTTS REST API"""

import httpx
import time
import base64
import io
import soundfile as sf
import sounddevice as sd

print("🧪 Testing XTTS REST API...")
print("=" * 50)

# API base URL
API_URL = "http://localhost:8127"

# Test client
client = httpx.Client(timeout=30.0)

# Test 1: Health check
print("\n1️⃣ Testing health endpoint...")
try:
    resp = client.get(f"{API_URL}/health")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Health: {data['status']}")
        print(f"   Engine: {data['engine']}")
    else:
        print(f"❌ Health check failed: {resp.status_code}")
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("   Make sure to run: python tts_servers/xtts_rest_api.py")
    exit(1)

# Test 2: List voices
print("\n2️⃣ Testing voices endpoint...")
resp = client.get(f"{API_URL}/v1/tts/voices")
if resp.status_code == 200:
    voices = resp.json()['voices']
    print(f"✅ Found {len(voices)} voices:")
    for v in voices:
        print(f"   - {v['id']}: {v['name']} ({v['language']})")

# Test 3: Synthesize to file
print("\n3️⃣ Testing synthesis to file...")
test_text = "Witaj w projekcie lbrxWhisper! To jest test syntezy mowy. No i zajebiście!"

resp = client.post(
    f"{API_URL}/v1/tts/synthesize",
    json={
        "text": test_text,
        "language": "pl",
        "voice": "female-pl-1",
        "speed": 1.0,
        "output_format": "wav"
    }
)

if resp.status_code == 200:
    result = resp.json()
    print(f"✅ Synthesized in {result['duration']:.2f}s")
    print(f"   Audio URL: {result['audio_url']}")
    
    # Download and play
    audio_resp = client.get(f"{API_URL}{result['audio_url']}")
    if audio_resp.status_code == 200:
        # Save to temp file
        with open("test_output.wav", "wb") as f:
            f.write(audio_resp.content)
        
        # Load and play
        audio_data, sample_rate = sf.read("test_output.wav")
        print("   🔊 Playing audio...")
        sd.play(audio_data, sample_rate)
        sd.wait()
        print("   ✅ Playback complete!")

# Test 4: Synthesize to base64
print("\n4️⃣ Testing synthesis to base64...")
resp = client.post(
    f"{API_URL}/v1/tts/synthesize",
    json={
        "text": "Test base64 encoding.",
        "language": "en",
        "output_format": "base64"
    }
)

if resp.status_code == 200:
    result = resp.json()
    print(f"✅ Got base64 audio")
    print(f"   Length: {len(result['audio_base64'])} chars")
    
    # Decode and check
    audio_bytes = base64.b64decode(result['audio_base64'])
    print(f"   Size: {len(audio_bytes) / 1024:.1f} KB")

print("\n" + "=" * 50)
print("🏁 Test complete!")
print("\nTo use in your code:")
print("```python")
print("import httpx")
print("client = httpx.Client()")
print("response = client.post('http://localhost:8127/v1/tts/synthesize', json={")
print("    'text': 'Cześć!', 'language': 'pl'")
print("})")
print("```")