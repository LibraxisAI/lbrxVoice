#!/usr/bin/env python3
"""
lbrxVoice Pipeline MVP
======================

Kompletny pipeline: Audio → ASR → LLM → TTS → Audio
dla analizy wizyt weterynaryjnych.

Autor: Maciej Gad & Claude
Data: 2025-05-30
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import soundfile as sf
import requests

# Komponenty
import mlx_whisper
from tools.whisper_config import WhisperConfig

# TTS
try:
    from mlx_audio.tts.generate import generate_audio as mlx_generate_audio
    HAS_MLX_AUDIO = True
except ImportError:
    HAS_MLX_AUDIO = False
    print("⚠️  MLX-Audio niedostępne - TTS wyłączone")


class VoicePipeline:
    """Pipeline głosowy dla Vista"""
    
    def __init__(
        self,
        whisper_model: str = "mlx-community/whisper-large-v3-mlx",
        llm_endpoint: str = "http://localhost:1234/v1/chat/completions",
        tts_model: str = "kokoro"
    ):
        self.whisper_model = whisper_model
        self.llm_endpoint = llm_endpoint
        self.tts_model = tts_model
        
        # Konfiguracja Whisper dla polskiego
        self.whisper_config = WhisperConfig.polish_optimized()
        
    async def process_audio(
        self,
        audio_path: str,
        output_dir: str = "outputs/pipeline",
        voice_response: bool = True
    ) -> Dict[str, Any]:
        """
        Przetwórz audio przez cały pipeline
        
        Args:
            audio_path: Ścieżka do pliku audio
            output_dir: Katalog na wyniki
            voice_response: Czy generować odpowiedź głosową
            
        Returns:
            Słownik z wynikami każdego etapu
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # 1. ASR - Transkrypcja
        print("\n🎤 Etap 1: Transkrypcja audio...")
        transcription = await self._transcribe_audio(audio_path)
        results['transcription'] = transcription
        
        # Zapisz transkrypcję
        trans_file = output_dir / "transcription.txt"
        trans_file.write_text(transcription['text'], encoding='utf-8')
        print(f"   Zapisano: {trans_file}")
        
        # 2. NLP/LLM - Analiza
        print("\n🧠 Etap 2: Analiza treści...")
        analysis = await self._analyze_text(transcription['text'])
        results['analysis'] = analysis
        
        # Zapisz analizę
        analysis_file = output_dir / "analysis.json"
        analysis_file.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"   Zapisano: {analysis_file}")
        
        # 3. TTS - Generuj odpowiedź głosową
        if voice_response and HAS_MLX_AUDIO:
            print("\n🔊 Etap 3: Generowanie odpowiedzi głosowej...")
            audio_file = await self._generate_speech(
                analysis.get('summary', 'Brak podsumowania'),
                output_dir
            )
            results['audio_response'] = str(audio_file)
            print(f"   Zapisano: {audio_file}")
        
        # 4. Podsumowanie
        print("\n✅ Pipeline zakończony!")
        results['status'] = 'completed'
        
        return results
    
    async def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transkrybuj audio używając Whisper MLX"""
        
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=self.whisper_model,
            **self.whisper_config.to_transcribe_kwargs()
        )
        
        return {
            'text': result['text'],
            'language': result.get('language', 'pl'),
            'segments': result.get('segments', [])
        }
    
    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analizuj tekst używając LLM"""
        
        # Prompt dla analizy weterynaryjnej
        prompt = f"""Jesteś asystentem weterynaryjnym. Przeanalizuj poniższą transkrypcję wizyty i wyodrębnij kluczowe informacje.

Transkrypcja:
{text}

Wyodrębnij:
1. Główne objawy/problemy
2. Wykonane badania
3. Diagnoza
4. Zalecone leczenie
5. Zalecenia dla właściciela

Odpowiedz w formacie JSON."""

        try:
            # Wywołaj LLM
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": "qwen3-8b-mlx",
                    "messages": [
                        {"role": "system", "content": "Jesteś pomocnym asystentem weterynaryjnym. Odpowiadaj zwięźle po polsku."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']
                
                # Sprawdź czy jest content czy reasoning_content
                content = message.get('content', '')
                if not content and 'reasoning_content' in message:
                    # Qwen3 czasem zwraca reasoning zamiast content
                    content = message['reasoning_content']
                    print("   ⚠️  Model zwrócił reasoning zamiast content")
                
                # Jeśli nadal pusty, użyj fallback
                if not content:
                    content = "Brak odpowiedzi od modelu"
                
                # Spróbuj sparsować jako JSON
                try:
                    analysis = json.loads(content)
                except:
                    # Jeśli nie JSON, zwróć jako tekst
                    analysis = {"summary": content}
                    
                return analysis
            else:
                return {
                    "error": f"LLM error: {response.status_code}",
                    "summary": "Nie udało się przeanalizować tekstu"
                }
                
        except Exception as e:
            print(f"   ⚠️  Błąd LLM: {e}")
            return {
                "error": str(e),
                "summary": "Analiza niedostępna - błąd połączenia z LLM"
            }
    
    async def _generate_speech(self, text: str, output_dir: Path) -> Path:
        """Generuj mowę z tekstu"""
        
        # Use our XTTS implementation
        from tts_servers.xtts_mlx import SimpleXTTSMLX
        import soundfile as sf
        
        # Skróć tekst jeśli za długi
        if len(text) > 500:
            text = text[:497] + "..."
        
        # Initialize TTS
        tts = SimpleXTTSMLX()
        
        # Generate audio
        audio_data = tts.synthesize(
            text=text,
            language="pl",  # Polish
            voice="female-pl-1",
            speed=1.0
        )
        
        # Save audio
        output_file = output_dir / "response.wav"
        sf.write(str(output_file), audio_data, tts.sample_rate)
        
        return output_file


async def demo_pipeline():
    """Demo pipeline'u"""
    
    print("="*60)
    print("🎯 lbrxVoice Pipeline Demo")
    print("="*60)
    
    # Znajdź przykładowy plik audio
    test_files = list(Path("uploads").glob("*.m4a"))[:3]
    
    if not test_files:
        print("❌ Brak plików testowych w uploads/")
        return
    
    # Utwórz pipeline
    pipeline = VoicePipeline()
    
    # Przetwórz pierwszy plik
    audio_file = test_files[0]
    print(f"\n📁 Plik testowy: {audio_file}")
    
    # Uruchom pipeline
    results = await pipeline.process_audio(
        str(audio_file),
        output_dir=f"outputs/pipeline/{audio_file.stem}",
        voice_response=HAS_MLX_AUDIO
    )
    
    print("\n📊 Wyniki:")
    print(f"   Transkrypcja: {len(results['transcription']['text'])} znaków")
    print(f"   Język: {results['transcription']['language']}")
    if 'analysis' in results and 'summary' in results['analysis']:
        print(f"   Analiza: {results['analysis']['summary'][:100]}...")
    if 'audio_response' in results:
        print(f"   Audio: {results['audio_response']}")


def main():
    """Uruchom demo"""
    asyncio.run(demo_pipeline())


if __name__ == "__main__":
    main()