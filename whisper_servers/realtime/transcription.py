"""
Module for handling real-time transcriptions with the MLX Whisper model.
"""
import asyncio
import base64
import io
import numpy as np
import time
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator, Tuple, List
import os

import mlx_whisper
from pydantic import BaseModel, Field
import websockets

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger


class RealtimeTranscriptionService:
    """Service for handling real-time transcription using MLX Whisper."""
    
    def __init__(self):
        self._model_path = settings.MODELS_DIR / settings.REALTIME_MODEL
        self._model_loaded = False
        self._model = None
        self._buffer = []
        self._sample_rate = 16000  # Fixed sample rate for MLX Whisper
    
    async def load_model(self) -> None:
        """Load the MLX Whisper model if not already loaded."""
        if self._model_loaded:
            return
        
        logger.info(f"Loading MLX Whisper model for real-time transcription: {settings.REALTIME_MODEL}")
        
        try:
            # Check if model exists, otherwise try to download it from the Hugging Face Hub
            model_path_or_repo = str(self._model_path)
            if not self._model_path.exists():
                logger.info(f"Model not found locally, attempting to load from 'mlx-community/whisper-{settings.REALTIME_MODEL}'")
                model_path_or_repo = f"mlx-community/whisper-{settings.REALTIME_MODEL}"
            
            # Load model (use to_thread because model loading is CPU-bound)
            self._model = await asyncio.to_thread(mlx_whisper.load_model, model_path_or_repo)
            self._model_loaded = True
            logger.info(f"MLX Whisper model loaded successfully for real-time transcription")
        except Exception as e:
            logger.error(f"Failed to load MLX Whisper model for real-time transcription: {e}")
            raise
    
    async def process_audio_chunk(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process a chunk of audio data.
        
        Args:
            audio_data: Raw PCM audio data (16-bit, 16kHz, mono)
            
        Returns:
            Transcription result
        """
        # Ensure model is loaded
        await self.load_model()
        
        try:
            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio_data, np.int16).astype(np.float32) / 32768.0
            
            # Transcribe the audio chunk
            result = await asyncio.to_thread(
                mlx_whisper.transcribe,
                audio_array,
                model=self._model,
                path_or_hf_repo=None,  # Use already loaded model
                language=None,  # Auto-detect language
                word_timestamps=True,  # Include word-level timestamps
            )
            
            return result
        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {e}")
            raise
    
    async def process_base64_audio(self, base64_audio: str) -> Dict[str, Any]:
        """
        Process base64-encoded audio data.
        
        Args:
            base64_audio: Base64-encoded audio data
            
        Returns:
            Transcription result
        """
        try:
            # Decode base64 data
            audio_data = base64.b64decode(base64_audio)
            
            # Process the audio data
            return await self.process_audio_chunk(audio_data)
        except Exception as e:
            logger.error(f"Error processing base64 audio: {e}")
            raise
    
    async def transcribe_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Transcribe an audio stream in real-time.
        
        Args:
            audio_stream: Async generator that yields audio chunks
            
        Yields:
            Transcription results for each chunk
        """
        # Ensure model is loaded
        await self.load_model()
        
        async for audio_chunk in audio_stream:
            result = await self.process_audio_chunk(audio_chunk)
            yield result
    
    async def transcribe_websocket(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """
        Handle WebSocket connection for real-time transcription.
        
        Args:
            websocket: WebSocket connection
        """
        # Ensure model is loaded
        await self.load_model()
        
        try:
            async for message in websocket:
                # Parse the incoming message
                if isinstance(message, str):
                    try:
                        import json
                        data = json.loads(message)
                        audio_base64 = data.get("audio")
                        if audio_base64:
                            # Process the audio data
                            result = await self.process_base64_audio(audio_base64)
                            
                            # Send the result back
                            await websocket.send(json.dumps({
                                "text": result.get("text", ""),
                                "language": result.get("language", ""),
                                "segments": result.get("segments", []),
                                "words": result.get("words", []),
                            }))
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON message")
                        await websocket.send(json.dumps({"error": "Invalid JSON message"}))
                elif isinstance(message, bytes):
                    # Process the raw audio data
                    result = await self.process_audio_chunk(message)
                    
                    # Send the result back
                    await websocket.send(json.dumps({
                        "text": result.get("text", ""),
                        "language": result.get("language", ""),
                        "segments": result.get("segments", []),
                        "words": result.get("words", []),
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
            try:
                await websocket.send(json.dumps({"error": str(e)}))
            except:
                pass


# Create a global instance of the real-time transcription service
transcription_service = RealtimeTranscriptionService()
