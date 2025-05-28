"""
REST API server for DIA TTS
"""

import asyncio
import base64
import io
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from ..common.config import config
from ..common.models import (
    TTSRequest, TTSResponse, TTSError, VoiceCloneRequest,
    AudioFormat, TTSModel
)
from .mlx_model import DiaMLX


app = FastAPI(title="DIA TTS REST API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
dia_model: Optional[DiaMLX] = None

# Job tracking
tts_jobs = {}


async def initialize_model():
    """Initialize DIA model"""
    global dia_model
    if dia_model is None:
        print("Initializing DIA MLX model...")
        dia_model = DiaMLX()
        dia_model.load_model()
        print("DIA model initialized")


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    await initialize_model()


def save_audio(audio_data: np.ndarray, format: AudioFormat, output_path: Path) -> Path:
    """Save audio data to file"""
    if format == AudioFormat.WAV:
        sf.write(output_path, audio_data, config.sample_rate, format='WAV')
    elif format == AudioFormat.FLAC:
        sf.write(output_path, audio_data, config.sample_rate, format='FLAC')
    elif format == AudioFormat.MP3:
        # First save as WAV, then convert to MP3
        wav_path = output_path.with_suffix('.wav')
        sf.write(wav_path, audio_data, config.sample_rate, format='WAV')
        # TODO: Use ffmpeg to convert to MP3
        output_path = wav_path  # For now, return WAV
    
    return output_path


async def process_tts_job(request: TTSRequest):
    """Process TTS job in background"""
    
    start_time = time.time()
    job_id = request.request_id
    
    try:
        # Update job status
        tts_jobs[job_id] = {"status": "processing", "progress": 0}
        
        # Generate audio codes
        audio_codes = dia_model.generate(
            text=request.text,
            temperature=request.temperature or config.temperature,
            top_p=request.top_p or config.top_p
        )
        
        tts_jobs[job_id]["progress"] = 50
        
        # Convert to audio waveform
        audio_data = dia_model.codes_to_audio(audio_codes, sample_rate=config.sample_rate)
        
        tts_jobs[job_id]["progress"] = 80
        
        # Save audio file
        output_filename = f"{job_id}.{request.audio_format.value}"
        output_path = config.output_dir / output_filename
        save_audio(audio_data, request.audio_format, output_path)
        
        # Create response
        processing_time = time.time() - start_time
        response = TTSResponse(
            request_id=job_id,
            audio_url=f"/audio/{output_filename}",
            duration=len(audio_data) / config.sample_rate,
            sample_rate=config.sample_rate,
            format=request.audio_format,
            model=request.model,
            processing_time=processing_time
        )
        
        tts_jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "response": response.dict(),
            "output_path": str(output_path)
        }
        
    except Exception as e:
        tts_jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_text(request: TTSRequest, background_tasks: BackgroundTasks):
    """Synthesize text to speech"""
    
    # Validate request
    if len(request.text) > config.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length is {config.max_text_length} characters"
        )
    
    # Check if model is loaded
    if dia_model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not initialized"
        )
    
    # Add job to background tasks
    background_tasks.add_task(process_tts_job, request)
    
    # Return immediate response with job ID
    return JSONResponse(
        content={
            "request_id": request.request_id,
            "status": "processing",
            "message": "TTS job submitted. Use /status/{request_id} to check progress"
        },
        status_code=202
    )


@app.post("/synthesize_sync", response_model=TTSResponse)
async def synthesize_text_sync(request: TTSRequest):
    """Synchronous text to speech synthesis"""
    
    # Validate request
    if len(request.text) > config.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length is {config.max_text_length} characters"
        )
    
    start_time = time.time()
    
    try:
        # Generate audio
        audio_codes = dia_model.generate(
            text=request.text,
            temperature=request.temperature or config.temperature,
            top_p=request.top_p or config.top_p
        )
        
        # Convert to audio waveform
        audio_data = dia_model.codes_to_audio(audio_codes, sample_rate=config.sample_rate)
        
        # Convert to base64
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, config.sample_rate, format='WAV')
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        processing_time = time.time() - start_time
        
        return TTSResponse(
            request_id=request.request_id,
            audio_data=audio_base64,
            duration=len(audio_data) / config.sample_rate,
            sample_rate=config.sample_rate,
            format=request.audio_format,
            model=request.model,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )


@app.post("/voice_clone", response_model=TTSResponse)
async def voice_clone(request: VoiceCloneRequest, background_tasks: BackgroundTasks):
    """Clone voice from reference audio"""
    
    # TODO: Implement voice cloning
    # This requires:
    # 1. Decode reference audio from base64
    # 2. Process reference audio with transcript
    # 3. Generate target text in cloned voice
    
    raise HTTPException(
        status_code=501,
        detail="Voice cloning not yet implemented"
    )


@app.get("/status/{request_id}")
async def get_job_status(request_id: str):
    """Get TTS job status"""
    
    if request_id not in tts_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job_info = tts_jobs[request_id]
    
    if job_info["status"] == "completed":
        return job_info["response"]
    elif job_info["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=job_info["error"]
        )
    else:
        return {
            "request_id": request_id,
            "status": job_info["status"],
            "progress": job_info.get("progress", 0)
        }


@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Download generated audio file"""
    
    file_path = config.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )


@app.delete("/audio/{filename}")
async def delete_audio_file(filename: str):
    """Delete generated audio file"""
    
    file_path = config.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )
    
    file_path.unlink()
    return {"message": "File deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": "dia-1.6b",
        "model_loaded": dia_model is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "DIA TTS REST API",
        "version": "1.0.0",
        "endpoints": {
            "synthesize": "/synthesize",
            "synthesize_sync": "/synthesize_sync",
            "voice_clone": "/voice_clone",
            "status": "/status/{request_id}",
            "audio": "/audio/{filename}",
            "health": "/health"
        }
    }


def main():
    """Run the REST API server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.dia_rest_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()