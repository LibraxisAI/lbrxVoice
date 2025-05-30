#!/usr/bin/env python3
"""
Test MLX-Audio TTS
==================

Szybki test dostępnych modeli TTS w mlx-audio.
"""

import asyncio
import numpy as np
import soundfile as sf
from pathlib import Path

try:
    from mlx_audio.tts.generate import generate_audio
    HAS_MLX_AUDIO = True
    print("✅ mlx-audio dostępne")
except ImportError:
    HAS_MLX_AUDIO = False
    print("❌ mlx-audio niedostępne")


async def test_tts():
    """Test różnych modeli TTS"""
    
    if not HAS_MLX_AUDIO:
        print("Zainstaluj mlx-audio: pip install mlx-audio")
        return
    
    # Teksty testowe
    texts = {
        "pl": "Witaj świecie! To jest test systemu syntezy mowy w języku polskim.",
        "en": "Hello world! This is a test of speech synthesis system.",
    }
    
    # Dostępne modele w mlx-audio
    models = [
        "kokoro",  # Multilingual
        "spark",   # English
        "dia",     # Multilingual (jeśli dostępny)
    ]
    
    output_dir = Path("tts_outputs/mlx_audio_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for model_name in models:
        print(f"\n🎤 Testowanie modelu: {model_name}")
        
        for lang, text in texts.items():
            try:
                print(f"  Język: {lang}")
                print(f"  Tekst: {text}")
                
                # Generuj audio
                output_file = output_dir / f"{model_name}_{lang}.wav"
                
                # Używamy generate_audio z mlx_audio
                result = generate_audio(
                    text=text,
                    model=model_name,
                    voice="default",  # lub inne dostępne
                    speed=1.0,
                    file_name=str(output_file.stem),
                    output_dir=str(output_dir)
                )
                
                print(f"  ✅ Zapisano: {output_file}")
                
            except Exception as e:
                print(f"  ❌ Błąd dla {model_name}/{lang}: {e}")
    
    print("\n✅ Testy zakończone!")
    print(f"Pliki audio zapisane w: {output_dir}")


def simple_test():
    """Prosty test synchroniczny"""
    if not HAS_MLX_AUDIO:
        print("Brak mlx-audio")
        return
        
    from mlx_audio.tts.generate import generate_audio
    
    # Test podstawowy
    print("Generowanie audio...")
    
    generate_audio(
        text="Cześć! To jest test systemu mowy.",
        model="kokoro",  # lub "spark"
        voice="af_polish",  # sprawdzamy dostępne głosy
        speed=1.0,
        file_name="test_polski",
        output_dir="tts_outputs"
    )
    
    print("✅ Wygenerowano test_polski.wav")


if __name__ == "__main__":
    # Najpierw prosty test
    simple_test()
    
    # Potem pełne testy
    # asyncio.run(test_tts())