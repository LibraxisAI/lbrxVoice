"""
FastAPI application for the batch transcription server.
"""
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger
from whisper_servers.common.utils import save_upload_file, is_audio_file
from whisper_servers.batch.transcription import transcription_service, TranscriptionJob


class TranscriptionRequest(BaseModel):
    """Model for transcription API request parameters."""
    model: str = Field(default="whisper-large-v3", description="Model to use for transcription")
    prompt: Optional[str] = Field(default=None, description="Optional text to guide the model's style")
    response_format: str = Field(default="json", description="Response format: json, text, srt, vtt, or tsv")
    temperature: float = Field(default=0, description="Temperature for sampling")
    language: Optional[str] = Field(default=None, description="Language code, e.g., 'en'")
    word_timestamps: bool = Field(default=False, description="Include word-level timestamps")


class TranscriptionResponse(BaseModel):
    """Model for transcription API response."""
    task: str = "transcription"
    text: str
    language: str
    duration: float
    segments: Optional[List[Dict[str, Any]]] = None
    words: Optional[List[Dict[str, Any]]] = None


class JobResponse(BaseModel):
    """Model for job status API response."""
    id: str
    status: str
    created_at: float
    completed_at: Optional[float] = None
    error: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="MLX Whisper Batch Transcription API",
    description="API for batch transcription of audio files using MLX Whisper",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/v1/audio/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form("whisper-large-v3"),
    prompt: Optional[str] = Form(None),
    response_format: str = Form("json"),
    temperature: float = Form(0.0),
    language: Optional[str] = Form(None),
    word_timestamps: bool = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Transcribe an audio file using MLX Whisper.
    
    This endpoint is compatible with the OpenAI Whisper API.
    """
    # Validate file type
    if not file.filename or not is_audio_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(settings.SUPPORTED_FORMATS)}",
        )
    
    # Save uploaded file
    saved_file = await save_upload_file(file)
    
    try:
        # Create transcription job
        job = await transcription_service.create_job(
            input_file=saved_file,
            word_timestamps=word_timestamps,
            language=language,
            prompt=prompt,
            temperature=temperature,
        )
        
        # Wait for job to complete
        while job.status not in ["completed", "failed"]:
            await asyncio.sleep(0.5)
        
        if job.status == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {job.error}",
            )
        
        # Format response based on requested format
        if response_format == "json":
            if not job.result:
                raise HTTPException(
                    status_code=500,
                    detail="Transcription result is missing",
                )
            
            response = TranscriptionResponse(
                text=job.result.get("text", ""),
                language=job.result.get("language", ""),
                duration=job.result.get("duration", 0.0),
                segments=job.result.get("segments", []),
                words=job.result.get("words", []) if word_timestamps else None,
            )
            return response
        else:
            # For future implementation of other formats like srt, vtt, etc.
            raise HTTPException(
                status_code=400,
                detail=f"Response format '{response_format}' not yet implemented",
            )
    
    except Exception as e:
        logger.exception(f"Error during transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}",
        )


@app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get the status of a transcription job.
    """
    job = transcription_service.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
        )
    
    return JobResponse(
        id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.error,
    )


@app.get("/v1/jobs", response_model=List[JobResponse])
async def list_jobs():
    """
    List all transcription jobs.
    """
    jobs = transcription_service.list_jobs()
    
    return [
        JobResponse(
            id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            error=job.error,
        )
        for job in jobs
    ]


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
