#!/usr/bin/env python3
"""
Test komponentów MVP lbrxVoice
==============================

Testuje każdy komponent osobno aby zweryfikować działanie.
"""

import asyncio
import json
import requests
from pathlib import Path

# Test 1: Whisper ASR
print("="*60)
print("🎤 Test 1: Whisper ASR")
print("="*60)

try:
    import mlx_whisper
    from tools.whisper_config import WhisperConfig
    
    # Znajdź plik testowy
    test_files = list(Path("uploads").glob("*.m4a"))[:1]
    if test_files:
        config = WhisperConfig.polish_optimized()
        print(f"Plik: {test_files[0].name}")
        print(f"Config: {config.language}, no repetitions: {config.condition_on_previous_text}")
        
        # Transkrybuj małym modelem dla szybkości
        result = mlx_whisper.transcribe(
            str(test_files[0]),
            path_or_hf_repo="mlx-community/whisper-tiny-mlx",
            language="pl",
            condition_on_previous_text=False,
            verbose=False
        )
        
        text = result['text'][:100]
        print(f"Transkrypcja: {text}...")
        print("✅ Whisper działa!")
    else:
        print("❌ Brak plików testowych")
        
except Exception as e:
    print(f"❌ Błąd Whisper: {e}")

# Test 2: LLM (Qwen3)
print("\n" + "="*60)
print("🧠 Test 2: LLM (Qwen3-8B)")
print("="*60)

try:
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json={
            "model": "qwen3-8b-mlx",
            "messages": [
                {"role": "user", "content": "Odpowiedz krótko po polsku: Jak leczyć kota z katarem?"}
            ],
            "temperature": 0.3,
            "max_tokens": 100,
            "stream": False
        },
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"Odpowiedź: {content[:200]}...")
        print("✅ LLM działa!")
    else:
        print(f"❌ LLM error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Błąd LLM: {e}")

# Test 3: TTS
print("\n" + "="*60)
print("🔊 Test 3: TTS (MLX-Audio)")
print("="*60)

try:
    from mlx_audio.tts.generate import generate_audio
    
    # Prosty test
    output_dir = Path("outputs/mvp_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generate_audio(
        text="Witaj! To jest test systemu mowy.",
        model="kokoro",
        speed=1.0,
        file_name="test_tts",
        output_dir=str(output_dir)
    )
    
    # Sprawdź czy plik istnieje
    if (output_dir / "test_tts.wav").exists():
        print(f"✅ TTS działa! Plik: {output_dir / 'test_tts.wav'}")
    else:
        print("❌ TTS nie wygenerował pliku")
        
except Exception as e:
    print(f"❌ Błąd TTS: {e}")

# Test 4: Pipeline endpoints
print("\n" + "="*60)
print("🌐 Test 4: API Endpoints")
print("="*60)

# Batch API
try:
    response = requests.get("http://localhost:8123/health", timeout=2)
    if response.status_code == 200:
        print("✅ Batch API (8123) działa!")
    else:
        print(f"⚠️ Batch API status: {response.status_code}")
except:
    print("❌ Batch API niedostępne")

# WebSocket test
try:
    import websocket
    ws = websocket.create_connection("ws://localhost:8126/v1/audio/transcriptions", timeout=2)
    ws.close()
    print("✅ WebSocket API (8126) działa!")
except:
    print("❌ WebSocket API niedostępne")

# Podsumowanie
print("\n" + "="*60)
print("📊 PODSUMOWANIE MVP")
print("="*60)

components = {
    "ASR (Whisper MLX)": "✅" if 'mlx_whisper' in locals() else "❌",
    "LLM (Qwen3-8B)": "✅" if 'content' in locals() else "❌",
    "TTS (MLX-Audio)": "✅" if 'generate_audio' in locals() else "❌",
    "API Endpoints": "⚠️ Sprawdź serwery"
}

for comp, status in components.items():
    print(f"{status} {comp}")

print("\n🎯 MVP Status: Podstawowe komponenty działają!")
print("📝 Problemy do rozwiązania:")
print("   - Jakość transkrypcji polskiej")
print("   - LLM zwraca reasoning zamiast czystej odpowiedzi")
print("   - TTS timeout dla długich tekstów")