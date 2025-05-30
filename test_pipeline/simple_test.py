#!/usr/bin/env python3
"""
Simple test of speech pipeline
"""

import sys
import base64
import json
import os
from pathlib import Path

def test_whisper_directly():
    """Test Whisper transcription directly"""
    print("\n🧪 Test bezpośredni Whisper...")
    
    try:
        from mlx_whisper import transcribe
        
        # Test with existing audio file
        test_file = "mlx_whisper/assets/ls_test.flac"
        if Path(test_file).exists():
            print(f"📁 Znaleziono plik testowy: {test_file}")
            
            result = transcribe(
                test_file,
                path_or_hf_repo="mlx-community/whisper-tiny",
                language="en"
            )
            
            print(f"✅ Transkrypcja: {result['text']}")
            return True
        else:
            print("❌ Brak pliku testowego")
            return False
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_csm_generate():
    """Test CSM generation"""
    print("\n🧪 Test generacji CSM...")
    
    try:
        # Add CSM path
        sys.path.insert(0, "/Users/maciejgad/LIBRAXIS/csm-mlx")
        
        from mlx_lm.sample_utils import make_sampler
        from huggingface_hub import hf_hub_download
        from csm_mlx import CSM, csm_1b, generate
        import mlx.core as mx
        
        print("📦 Ładowanie modelu CSM...")
        csm = CSM(csm_1b())
        weight = hf_hub_download(repo_id="senstella/csm-1b-mlx", filename="ckpt.safetensors")
        csm.load_weights(weight)
        
        text = "Cześć! To jest test systemu syntezy mowy."
        print(f"🎤 Generowanie: '{text}'")
        
        audio = generate(
            csm,
            text=text,
            speaker=0,
            context=[],
            max_audio_length_ms=5000,
            sampler=make_sampler(temp=0.8, top_k=50)
        )
        
        print(f"✅ Wygenerowano audio: {audio.shape} próbek")
        
        # Save to file
        import soundfile as sf
        output_path = Path("test_pipeline/tts_outputs/csm_test.wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), audio, 16000)
        print(f"💾 Zapisano: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Błąd CSM: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pipeline():
    """Test full pipeline without servers"""
    print("\n🚀 Test pipeline bez serwerów")
    print("=" * 50)
    
    # 1. Test Whisper
    if test_whisper_directly():
        print("✅ Whisper działa")
    else:
        print("❌ Problem z Whisper")
        
    # 2. Test CSM 
    audio_file = test_csm_generate()
    
    if audio_file and Path(audio_file).exists():
        print("\n📝 Transkrypcja wygenerowanego audio...")
        
        try:
            from mlx_whisper import transcribe
            
            result = transcribe(
                audio_file,
                path_or_hf_repo="mlx-community/whisper-small",
                language="pl"  # Polish
            )
            
            print(f"✅ Transkrypcja: {result['text']}")
            
        except Exception as e:
            print(f"❌ Błąd transkrypcji: {e}")

def test_simple_servers():
    """Test simple server functionality"""
    print("\n🧪 Test prostych funkcji serwerowych...")
    
    # Test whisper server module
    try:
        from whisper_servers.batch.transcription import WhisperTranscriber
        print("✅ Whisper server module - OK")
    except Exception as e:
        print(f"❌ Whisper server module - {e}")
        
    # Test CSM server module  
    try:
        from tts_servers.common.models import TTSRequest
        print("✅ TTS common models - OK")
    except Exception as e:
        print(f"❌ TTS common models - {e}")

def main():
    print("🎯 lbrxVoice - Prosty test pipeline'u")
    
    # Create output dirs
    Path("test_pipeline/tts_outputs").mkdir(parents=True, exist_ok=True)
    Path("test_pipeline/whisper_outputs").mkdir(parents=True, exist_ok=True)
    
    # Run tests
    test_simple_servers()
    test_pipeline()
    
    print("\n✅ Test zakończony")

if __name__ == "__main__":
    main()