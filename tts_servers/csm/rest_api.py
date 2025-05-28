"""
REST API server for CSM-MLX TTS
"""

import asyncio
import base64
import io
import time
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Add CSM-MLX to path
sys.path.append("/Users/maciejgad/LIBRAXIS/csm-mlx")

from mlx_lm.sample_utils import make_sampler
from huggingface_hub import hf_hub_download
from csm_mlx import CSM, csm_1b, generate

from ..common.config import config
from ..common.models import (
    TTSRequest, TTSResponse, TTSError,
    AudioFormat, TTSModel
)


app = FastAPI(title="CSM-MLX TTS REST API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
csm_model: Optional[CSM] = None

# Job tracking
tts_jobs = {}


async def initialize_model():
    """Initialize CSM model"""
    global csm_model
    if csm_model is None:
        print("Initializing CSM-MLX model...")
        
        # Initialize the model
        csm_model = CSM(csm_1b())
        
        # Download and load weights
        weight_path = hf_hub_download(
            repo_id="senstella/csm-1b-mlx", 
            filename="ckpt.safetensors"
        )
        csm_model.load_weights(weight_path)
        
        print("CSM model initialized")


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    await initialize_model()


def save_audio(audio_data: np.ndarray, format: AudioFormat, output_path: Path) -> Path:
    """Save audio data to file"""
    if format == AudioFormat.WAV:
        sf.write(output_path, audio_data, 16000, format='WAV')  # CSM uses 16kHz
    elif format == AudioFormat.FLAC:
        sf.write(output_path, audio_data, 16000, format='FLAC')
    elif format == AudioFormat.MP3:
        # First save as WAV, then convert to MP3
        wav_path = output_path.with_suffix('.wav')
        sf.write(wav_path, audio_data, 16000, format='WAV')
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
        
        # Parse speaker ID (default to 0)
        speaker_id = int(request.speaker_id) if request.speaker_id else 0
        
        # Generate audio using CSM
        sampler_kwargs = {}
        if request.temperature is not None:
            sampler_kwargs["temp"] = request.temperature
        if request.top_p is not None:
            sampler_kwargs["top_p"] = request.top_p
        else:
            sampler_kwargs["top_k"] = 50  # Default top_k
            
        sampler = make_sampler(**sampler_kwargs)
        
        tts_jobs[job_id]["progress"] = 20
        
        audio_array = generate(
            csm_model,
            text=request.text,
            speaker=speaker_id,
            context=[],
            max_audio_length_ms=30_000,  # Max 30 seconds
            sampler=sampler
        )
        
        tts_jobs[job_id]["progress"] = 80
        
        # Save audio file
        output_filename = f"{job_id}.{request.audio_format.value}"
        output_path = config.output_dir / output_filename
        save_audio(audio_array, request.audio_format, output_path)
        
        # Create response
        processing_time = time.time() - start_time
        response = TTSResponse(
            request_id=job_id,
            audio_url=f"/audio/{output_filename}",
            duration=len(audio_array) / 16000,  # CSM uses 16kHz
            sample_rate=16000,
            format=request.audio_format,
            model=TTSModel.CSM_MLX,
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
    
    # Override model to CSM
    request.model = TTSModel.CSM_MLX
    
    # Validate request
    if len(request.text) > config.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length is {config.max_text_length} characters"
        )
    
    # Check if model is loaded
    if csm_model is None:
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
    
    # Override model to CSM
    request.model = TTSModel.CSM_MLX
    
    # Validate request
    if len(request.text) > config.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum length is {config.max_text_length} characters"
        )
    
    start_time = time.time()
    
    try:
        # Parse speaker ID (default to 0)
        speaker_id = int(request.speaker_id) if request.speaker_id else 0
        
        # Generate audio using CSM
        sampler_kwargs = {}
        if request.temperature is not None:
            sampler_kwargs["temp"] = request.temperature
        if request.top_p is not None:
            sampler_kwargs["top_p"] = request.top_p
        else:
            sampler_kwargs["top_k"] = 50  # Default top_k
            
        sampler = make_sampler(**sampler_kwargs)
        
        audio_array = generate(
            csm_model,
            text=request.text,
            speaker=speaker_id,
            context=[],
            max_audio_length_ms=30_000,  # Max 30 seconds
            sampler=sampler
        )
        
        # Convert to base64
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, 16000, format='WAV')
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        processing_time = time.time() - start_time
        
        return TTSResponse(
            request_id=request.request_id,
            audio_data=audio_base64,
            duration=len(audio_array) / 16000,
            sample_rate=16000,
            format=request.audio_format,
            model=TTSModel.CSM_MLX,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
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


@app.get("/speakers")
async def get_available_speakers():
    """Get available speaker IDs"""
    return {
        "speakers": [
            {"id": 0, "name": "Speaker 0", "description": "Default speaker"},
            {"id": 1, "name": "Speaker 1", "description": "Alternative speaker 1"},
            {"id": 2, "name": "Speaker 2", "description": "Alternative speaker 2"},
            {"id": 3, "name": "Speaker 3", "description": "Alternative speaker 3"},
        ],
        "note": "CSM supports multiple speakers. Experiment to find the voice you prefer."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": "csm-1b-mlx",
        "model_loaded": csm_model is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CSM-MLX TTS REST API",
        "version": "1.0.0",
        "endpoints": {
            "synthesize": "/synthesize",
            "synthesize_sync": "/synthesize_sync",
            "status": "/status/{request_id}",
            "audio": "/audio/{filename}",
            "speakers": "/speakers",
            "health": "/health"
        }
    }


def main():
    """Run the REST API server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.csm_rest_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()