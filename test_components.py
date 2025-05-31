#!/usr/bin/env python3
"""
Test basic components to diagnose issues
"""

import sys
import asyncio
from pathlib import Path

print("🧪 Testing lbrxWhisper components...")
print("=" * 50)

# Test 1: Whisper servers
print("\n1️⃣ Testing Whisper servers...")
try:
    import httpx
    client = httpx.Client(timeout=2.0)
    
    # Batch API
    resp = client.get("http://localhost:8123/health")
    if resp.status_code == 200:
        print("✅ Whisper Batch API: OK")
    else:
        print(f"❌ Whisper Batch API: {resp.status_code}")
except Exception as e:
    print(f"❌ Whisper Batch API: {e}")

# Test 2: LM Studio
print("\n2️⃣ Testing LM Studio...")
try:
    resp = client.get("http://localhost:1234/v1/models")
    if resp.status_code == 200:
        models = resp.json()
        print(f"✅ LM Studio: OK - {len(models.get('data', []))} models loaded")
        for model in models.get('data', []):
            print(f"   - {model.get('id', 'unknown')}")
    else:
        print(f"❌ LM Studio: {resp.status_code}")
except Exception as e:
    print(f"❌ LM Studio: {e}")

# Test 3: Audio recording
print("\n3️⃣ Testing audio recording...")
try:
    import sounddevice as sd
    devices = sd.query_devices()
    input_devices = [d for d in devices if d['max_input_channels'] > 0]
    print(f"✅ Found {len(input_devices)} input devices")
    for d in input_devices[:3]:
        print(f"   - {d['name']}")
except Exception as e:
    print(f"❌ Audio recording: {e}")

# Test 4: MLX
print("\n4️⃣ Testing MLX...")
try:
    import mlx
    import mlx_whisper
    print("✅ MLX: OK")
    print("✅ MLX Whisper: OK")
except Exception as e:
    print(f"❌ MLX: {e}")

# Test 5: TTS
print("\n5️⃣ Testing TTS...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from tts_servers.xtts_mlx import SimpleXTTSMLX
    print("✅ XTTS MLX: OK (our implementation)")
except Exception as e:
    print(f"❌ XTTS MLX: {e}")

# Test 6: Test simple chat with LM Studio
print("\n6️⃣ Testing LM Studio chat...")
try:
    test_prompt = {
        "model": "qwen3-8b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello test' and nothing else."}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }
    
    resp = client.post(
        "http://localhost:1234/v1/chat/completions",
        json=test_prompt,
        timeout=10.0
    )
    
    if resp.status_code == 200:
        result = resp.json()
        content = result['choices'][0]['message']['content']
        print(f"✅ LM Studio chat: '{content}'")
    else:
        print(f"❌ LM Studio chat: {resp.status_code}")
except Exception as e:
    print(f"❌ LM Studio chat: {e}")

print("\n" + "=" * 50)
print("🏁 Test complete!")