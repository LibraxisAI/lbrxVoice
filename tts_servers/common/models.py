"""Common data models for TTS servers"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class TTSModel(str, Enum):
    """Available TTS models"""
    DIA_16B = "dia-1.6b"
    CSM_MLX = "csm-mlx"


class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"


class TTSRequest(BaseModel):
    """TTS synthesis request"""
    text: str = Field(..., description="Text to synthesize")
    model: TTSModel = Field(default=TTSModel.DIA_16B, description="TTS model to use")
    speaker_id: Optional[str] = Field(default=None, description="Speaker ID for voice")
    audio_format: AudioFormat = Field(default=AudioFormat.WAV, description="Output audio format")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")
    top_p: Optional[float] = Field(default=None, description="Top-p sampling")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Pitch adjustment")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    

class TTSResponse(BaseModel):
    """TTS synthesis response"""
    request_id: str
    audio_url: Optional[str] = None
    audio_data: Optional[str] = None  # Base64 encoded audio
    duration: float
    sample_rate: int
    format: AudioFormat
    model: TTSModel
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TTSStreamChunk(BaseModel):
    """Streaming TTS chunk"""
    request_id: str
    chunk_index: int
    audio_data: str  # Base64 encoded audio chunk
    is_final: bool = False
    timestamp: float


class VoiceCloneRequest(BaseModel):
    """Voice cloning request for DIA"""
    reference_audio: str  # Base64 encoded reference audio
    reference_transcript: str  # Transcript of reference audio
    target_text: str  # Text to synthesize in cloned voice
    audio_format: AudioFormat = Field(default=AudioFormat.WAV)
    

class TTSError(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)