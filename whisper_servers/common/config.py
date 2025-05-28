"""
Configuration settings for the MLX Whisper servers.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ServerSettings(BaseSettings):
    """Server configuration settings with environment variable support."""
    # Server ports
    BATCH_PORT: int = Field(default=8123)
    REALTIME_PORT: int = Field(default=8000)
    
    # Model settings
    MODELS_DIR: Path = Field(default=Path("models"))
    BATCH_MODEL: str = Field(default="large-v3")
    REALTIME_MODEL: str = Field(default="tiny")
    
    # Audio settings
    MAX_AUDIO_SIZE_MB: int = Field(default=100)
    SUPPORTED_FORMATS: List[str] = Field(
        default=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    )
    
    # File storage
    UPLOAD_DIR: Path = Field(default=Path("uploads"))
    RESULTS_DIR: Path = Field(default=Path("results"))
    
    # Processing settings
    MAX_CONCURRENT_JOBS: int = Field(default=2)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_prefix=""
    )


# Create a global settings instance
settings = ServerSettings()

# Ensure directories exist
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
