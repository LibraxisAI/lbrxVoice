"""Configuration for TTS servers"""

import os
from pathlib import Path
from pydantic import BaseSettings, Field


class TTSConfig(BaseSettings):
    """TTS Server Configuration"""
    
    # Model settings
    dia_model_path: str = Field(default="./models/dia_mlx", env="DIA_MODEL_PATH")
    csm_model_path: str = Field(default="./models/csm_mlx", env="CSM_MODEL_PATH")
    
    # Server settings
    dia_ws_port: int = Field(default=8129, env="DIA_WS_PORT")
    dia_rest_port: int = Field(default=8132, env="DIA_REST_PORT")
    csm_rest_port: int = Field(default=8135, env="CSM_REST_PORT")
    
    # Audio settings
    sample_rate: int = Field(default=44100, env="TTS_SAMPLE_RATE")
    audio_format: str = Field(default="wav", env="TTS_AUDIO_FORMAT")
    
    # Processing settings
    max_text_length: int = Field(default=1000, env="TTS_MAX_TEXT_LENGTH")
    temperature: float = Field(default=0.8, env="TTS_TEMPERATURE")
    top_p: float = Field(default=0.95, env="TTS_TOP_P")
    
    # Paths
    output_dir: Path = Field(default=Path("./tts_outputs"), env="TTS_OUTPUT_DIR")
    temp_dir: Path = Field(default=Path("./tts_temp"), env="TTS_TEMP_DIR")
    
    # Performance
    max_concurrent_requests: int = Field(default=5, env="TTS_MAX_CONCURRENT")
    request_timeout: int = Field(default=300, env="TTS_REQUEST_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = TTSConfig()