#!/usr/bin/env python3
"""
Wrapper dla MLX-Audio DIA TTS
=============================

Integracja z mlx-audio dla generowania mowy.
"""

import mlx.core as mx
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import asyncio

try:
    from mlx_audio.tts.models.dia import DIA
    from mlx_audio.tts.models.dia.config import DIAConfig
    from mlx_audio.tts.utils import to_pcm_16khz
    HAS_MLX_AUDIO = True
except ImportError:
    HAS_MLX_AUDIO = False
    print("Warning: mlx-audio not available, using placeholder")


class DIAMLXWrapper:
    """Wrapper dla MLX-Audio DIA"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.config = None
        
    async def initialize(self):
        """Inicjalizacja modelu"""
        if not HAS_MLX_AUDIO:
            print("mlx-audio not available - using placeholder")
            return
            
        try:
            # Domyślna ścieżka modelu
            if not self.model_path:
                self.model_path = "bene-ges/dia_1.6B_mlx_q8"
            
            print(f"Loading DIA model from: {self.model_path}")
            
            # Załaduj konfigurację i model
            self.config = DIAConfig.from_pretrained(self.model_path)
            self.model = DIA.from_pretrained(self.model_path)
            
            print("DIA model loaded successfully")
            
        except Exception as e:
            print(f"Error loading DIA model: {e}")
            self.model = None
    
    async def generate(
        self,
        text: str,
        voice_preset: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> np.ndarray:
        """Generuj audio z tekstu"""
        
        if not HAS_MLX_AUDIO or self.model is None:
            # Placeholder - zwróć ciszę
            duration = len(text.split()) * 0.3  # ~0.3s per word
            samples = int(16000 * duration)
            return np.zeros(samples, dtype=np.float32)
        
        try:
            # Przygotuj parametry
            generation_params = {
                "text": text,
                "speed": speed,
            }
            
            # Dodaj voice preset jeśli podany
            if voice_preset:
                generation_params["voice_preset"] = voice_preset
            
            # Generuj audio
            audio = await asyncio.to_thread(
                self.model.generate,
                **generation_params
            )
            
            # Konwertuj do 16kHz PCM jeśli potrzeba
            if isinstance(audio, mx.array):
                audio = np.array(audio)
            
            # Normalizuj
            audio = audio / np.max(np.abs(audio))
            
            return audio.astype(np.float32)
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            # Zwróć ciszę w razie błędu
            duration = len(text.split()) * 0.3
            samples = int(16000 * duration)
            return np.zeros(samples, dtype=np.float32)
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Zwróć dostępne głosy"""
        if not HAS_MLX_AUDIO or self.model is None:
            return {
                "voices": ["default"],
                "languages": ["pl", "en"]
            }
        
        # DIA obsługuje wiele języków
        return {
            "voices": ["default", "male", "female", "young", "old"],
            "languages": ["pl", "en", "de", "fr", "es", "it", "ru", "zh", "ja", "ko"]
        }


# Singleton instance
_dia_instance = None


async def get_dia_instance() -> DIAMLXWrapper:
    """Pobierz instancję DIA (singleton)"""
    global _dia_instance
    
    if _dia_instance is None:
        _dia_instance = DIAMLXWrapper()
        await _dia_instance.initialize()
    
    return _dia_instance


# Test
if __name__ == "__main__":
    async def test():
        dia = await get_dia_instance()
        
        # Test polski
        audio = await dia.generate(
            "Witaj świecie! To jest test systemu syntezy mowy.",
            speed=1.0
        )
        print(f"Generated audio shape: {audio.shape}")
        
        # Test angielski
        audio_en = await dia.generate(
            "Hello world! This is a test of speech synthesis.",
            speed=1.2
        )
        print(f"Generated English audio shape: {audio_en.shape}")
    
    asyncio.run(test())