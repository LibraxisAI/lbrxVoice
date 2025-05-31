#!/usr/bin/env python3
"""
REST API server for XTTS MLX
Provides HTTP endpoints for TTS synthesis
"""

import asyncio
import base64
import io
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import soundfile as sf

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Import our XTTS implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tts_servers.xtts_mlx import SimpleXTTSMLX


class TTSRequest(BaseModel):
    text: str
    language: str = "pl"
    voice: str = "female-pl-1"
    speed: float = 1.0
    output_format: str = "wav"  # wav, mp3, base64


class TTSResponse(BaseModel):
    id: str
    status: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    duration: Optional[float] = None
    message: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="XTTS MLX API",
    description="Text-to-Speech API using XTTS v2 on MLX",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global TTS instance
tts_engine = None


@app.on_event("startup")
async def startup():
    """Initialize TTS engine on startup"""
    global tts_engine
    print("🚀 Initializing XTTS MLX engine...")
    tts_engine = SimpleXTTSMLX()
    print("✅ XTTS MLX engine ready!")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "XTTS MLX API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "synthesize": "/v1/tts/synthesize",
            "voices": "/v1/tts/voices",
            "languages": "/v1/tts/languages"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine": "xtts-mlx",
        "ready": tts_engine is not None
    }


@app.get("/v1/tts/voices")
async def list_voices():
    """List available voices"""
    return {
        "voices": [
            {"id": "female-pl-1", "name": "Polish Female 1", "language": "pl"},
            {"id": "male-pl-1", "name": "Polish Male 1", "language": "pl"},
            {"id": "female-en-1", "name": "English Female 1", "language": "en"},
            {"id": "male-en-1", "name": "English Male 1", "language": "en"},
        ]
    }


@app.get("/v1/tts/languages")
async def list_languages():
    """List supported languages"""
    return {
        "languages": [
            {"code": "pl", "name": "Polish"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
        ]
    }


@app.post("/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize(request: TTSRequest, background_tasks: BackgroundTasks):
    """Synthesize speech from text"""
    
    if not tts_engine:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")
    
    # Generate unique ID
    synthesis_id = str(uuid.uuid4())
    
    try:
        # Synthesize audio
        start_time = time.time()
        
        print(f"🎤 Synthesizing: '{request.text[:50]}...' [{request.language}]")
        
        audio_data = tts_engine.synthesize(
            text=request.text,
            language=request.language,
            voice=request.voice,
            speed=request.speed
        )
        
        duration = time.time() - start_time
        
        # Handle output format
        if request.output_format == "base64":
            # Convert to base64
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, tts_engine.sample_rate, format='WAV')
            buffer.seek(0)
            audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            return TTSResponse(
                id=synthesis_id,
                status="completed",
                audio_base64=audio_base64,
                duration=duration
            )
            
        else:
            # Save to file
            output_dir = Path("outputs/tts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{synthesis_id}.wav"
            filepath = output_dir / filename
            
            sf.write(str(filepath), audio_data, tts_engine.sample_rate)
            
            # Clean up old files in background
            background_tasks.add_task(cleanup_old_files, output_dir)
            
            return TTSResponse(
                id=synthesis_id,
                status="completed",
                audio_url=f"/v1/tts/audio/{filename}",
                duration=duration
            )
            
    except Exception as e:
        print(f"❌ Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tts/audio/{filename}")
async def get_audio(filename: str):
    """Serve synthesized audio file"""
    filepath = Path("outputs/tts") / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=filename
    )


async def cleanup_old_files(directory: Path, max_age_hours: int = 1):
    """Clean up old audio files"""
    try:
        now = time.time()
        for file in directory.glob("*.wav"):
            if (now - file.stat().st_mtime) > (max_age_hours * 3600):
                file.unlink()
    except:
        pass


def main():
    """Run the TTS API server"""
    print("""
    ╔═══════════════════════════════════════╗
    ║         XTTS MLX REST API             ║
    ║   Text-to-Speech Service on MLX       ║
    ╚═══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8127,  # New port for XTTS
        log_level="info"
    )


if __name__ == "__main__":
    main()