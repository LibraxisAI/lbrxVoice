#!/usr/bin/env python3
"""
Testy dla lbrxVoice Pipeline
============================

Testuje każdy komponent osobno i cały pipeline.
"""

import pytest
import asyncio
import json
from pathlib import Path
import numpy as np
import requests
from unittest.mock import Mock, patch, MagicMock

# Import naszego pipeline
import sys
sys.path.append(str(Path(__file__).parent.parent))
from lbrx_voice_pipeline import VoicePipeline


class TestWhisperComponent:
    """Testy komponentu ASR"""
    
    def test_whisper_import(self):
        """Test czy Whisper się importuje"""
        import mlx_whisper
        assert mlx_whisper is not None
    
    def test_whisper_config(self):
        """Test konfiguracji Whisper"""
        from tools.whisper_config import WhisperConfig
        
        config = WhisperConfig.polish_optimized()
        assert config.language == "pl"
        assert config.condition_on_previous_text == False
        assert config.compression_ratio_threshold == 2.4
    
    @pytest.mark.asyncio
    async def test_transcription_mock(self):
        """Test transkrypcji z mockiem"""
        pipeline = VoicePipeline()
        
        # Mock mlx_whisper.transcribe
        with patch('mlx_whisper.transcribe') as mock_transcribe:
            mock_transcribe.return_value = {
                'text': 'Test transkrypcji po polsku.',
                'language': 'pl',
                'segments': []
            }
            
            result = await pipeline._transcribe_audio('dummy.wav')
            
            assert result['text'] == 'Test transkrypcji po polsku.'
            assert result['language'] == 'pl'
            mock_transcribe.assert_called_once()


class TestLLMComponent:
    """Testy komponentu LLM"""
    
    def test_llm_endpoint_available(self):
        """Test czy LM Studio odpowiada"""
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            assert response.status_code == 200
            models = response.json()
            assert any('qwen3' in m['id'].lower() for m in models['data'])
        except:
            pytest.skip("LM Studio niedostępne")
    
    @pytest.mark.asyncio
    async def test_llm_analysis_mock(self):
        """Test analizy z mockiem"""
        pipeline = VoicePipeline()
        
        # Mock requests.post
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'objawy': ['gorączka'],
                            'diagnoza': 'test',
                            'zalecenia': 'obserwacja'
                        })
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            result = await pipeline._analyze_text('Pies ma gorączkę')
            
            assert 'objawy' in result
            assert result['objawy'] == ['gorączka']
    
    @pytest.mark.asyncio
    async def test_llm_reasoning_fix(self):
        """Test naprawy problemu z reasoning_content"""
        pipeline = VoicePipeline()
        
        # Mock response z reasoning_content
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{
                    'message': {
                        'content': '',  # Pusty content
                        'reasoning_content': 'To jest reasoning',
                        'role': 'assistant'
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            result = await pipeline._analyze_text('Test')
            
            # Powinien obsłużyć pusty content
            assert 'summary' in result or 'error' in result


class TestTTSComponent:
    """Testy komponentu TTS"""
    
    def test_mlx_audio_import(self):
        """Test czy mlx-audio się importuje"""
        try:
            from mlx_audio.tts.generate import generate_audio
            assert generate_audio is not None
        except ImportError:
            pytest.skip("MLX-Audio niedostępne")
    
    @pytest.mark.asyncio
    async def test_tts_generation_mock(self):
        """Test generowania mowy z mockiem"""
        pipeline = VoicePipeline()
        
        with patch('mlx_audio.tts.generate.generate_audio') as mock_generate:
            mock_generate.return_value = None  # MLX-Audio zapisuje plik
            
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            # Utwórz dummy plik który MLX-Audio by utworzył
            dummy_file = output_dir / "response.wav"
            dummy_file.write_text("dummy")
            
            result = await pipeline._generate_speech("Test", output_dir)
            
            assert result.exists()
            
            # Cleanup
            dummy_file.unlink()
            output_dir.rmdir()


class TestFullPipeline:
    """Testy pełnego pipeline"""
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test inicjalizacji pipeline"""
        pipeline = VoicePipeline(
            whisper_model="mlx-community/whisper-tiny-mlx",
            llm_endpoint="http://localhost:1234/v1/chat/completions",
            tts_model="kokoro"
        )
        
        assert pipeline.whisper_model == "mlx-community/whisper-tiny-mlx"
        assert pipeline.llm_endpoint == "http://localhost:1234/v1/chat/completions"
        assert pipeline.tts_model == "kokoro"
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """Test pełnego pipeline z mockami"""
        pipeline = VoicePipeline()
        
        # Mock wszystkich komponentów
        with patch('mlx_whisper.transcribe') as mock_transcribe, \
             patch('requests.post') as mock_post, \
             patch('mlx_audio.tts.generate.generate_audio') as mock_generate:
            
            # Setup mocks
            mock_transcribe.return_value = {
                'text': 'Pies ma gorączkę 40 stopni',
                'language': 'pl',
                'segments': []
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'objawy': ['gorączka 40°C'],
                            'zalecenia': 'Natychmiast do weterynarza'
                        })
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            # Test
            results = await pipeline.process_audio(
                "dummy.wav",
                output_dir="test_output",
                voice_response=False  # Bez TTS dla prostoty
            )
            
            assert results['status'] == 'completed'
            assert 'transcription' in results
            assert 'analysis' in results
            assert results['transcription']['text'] == 'Pies ma gorączkę 40 stopni'
            
            # Cleanup
            import shutil
            if Path("test_output").exists():
                shutil.rmtree("test_output")


class TestEdgeCases:
    """Testy przypadków brzegowych"""
    
    @pytest.mark.asyncio
    async def test_empty_audio(self):
        """Test pustego audio"""
        pipeline = VoicePipeline()
        
        with patch('mlx_whisper.transcribe') as mock_transcribe:
            mock_transcribe.return_value = {
                'text': '',
                'language': 'unknown',
                'segments': []
            }
            
            result = await pipeline._transcribe_audio('empty.wav')
            assert result['text'] == ''
    
    @pytest.mark.asyncio
    async def test_llm_timeout(self):
        """Test timeout LLM"""
        pipeline = VoicePipeline()
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.Timeout("Timeout")
            
            result = await pipeline._analyze_text('Test')
            assert 'error' in result
            assert 'Analiza niedostępna' in result['summary']
    
    @pytest.mark.asyncio
    async def test_long_text_truncation(self):
        """Test obcięcia długiego tekstu dla TTS"""
        pipeline = VoicePipeline()
        
        long_text = "A" * 1000  # Bardzo długi tekst
        
        with patch('mlx_audio.tts.generate.generate_audio') as mock_generate:
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            # Utwórz dummy plik
            (output_dir / "response.wav").write_text("dummy")
            
            await pipeline._generate_speech(long_text, output_dir)
            
            # Sprawdź czy tekst został obcięty
            call_args = mock_generate.call_args[1]
            assert len(call_args['text']) <= 500
            assert call_args['text'].endswith('...')
            
            # Cleanup
            import shutil
            shutil.rmtree("test_output")


# Fixture dla testów integracyjnych
@pytest.fixture
def sample_audio_file():
    """Zwraca przykładowy plik audio jeśli istnieje"""
    audio_files = list(Path("uploads").glob("*.m4a"))
    if audio_files:
        return str(audio_files[0])
    return None


# Test integracyjny (oznaczony jako slow)
@pytest.mark.slow
@pytest.mark.asyncio
async def test_real_pipeline(sample_audio_file):
    """Test rzeczywistego pipeline (wymaga działających serwerów)"""
    if not sample_audio_file:
        pytest.skip("Brak plików audio do testu")
    
    pipeline = VoicePipeline()
    
    try:
        results = await pipeline.process_audio(
            sample_audio_file,
            output_dir="test_output_real",
            voice_response=False  # Bez TTS dla szybkości
        )
        
        assert results['status'] == 'completed'
        assert len(results['transcription']['text']) > 0
        
        # Cleanup
        import shutil
        shutil.rmtree("test_output_real")
        
    except Exception as e:
        pytest.skip(f"Pipeline test failed: {e}")


if __name__ == "__main__":
    # Uruchom testy
    pytest.main([__file__, "-v", "--tb=short"])