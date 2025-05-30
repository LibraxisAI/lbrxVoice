#!/usr/bin/env python3
"""
Test mlx-audio with DIA model
"""

from mlx_audio import TTS, STS

# Test TTS with DIA
def test_dia():
    print("🎙️ Testing DIA with mlx-audio...")
    
    # Initialize TTS with DIA model
    tts = TTS(model="dia-1.6b")
    
    # Test synthesis
    text = "[S1] Hello from MLX Audio! [S2] This is amazing technology."
    
    print(f"Synthesizing: {text}")
    audio = tts.synthesize(text)
    
    # Save audio
    output_path = "./test_outputs/dia_mlx_audio_test.wav"
    tts.save_audio(audio, output_path)
    
    print(f"✅ Audio saved to: {output_path}")
    

if __name__ == "__main__":
    test_dia()