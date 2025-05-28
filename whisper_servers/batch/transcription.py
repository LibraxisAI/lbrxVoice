"""
Module for handling batch transcriptions with the MLX Whisper large-v3 model.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import os
import time

import mlx_whisper
from pydantic import BaseModel, Field

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger
from whisper_servers.common.utils import convert_to_wav, generate_unique_id


class TranscriptionJob(BaseModel):
    """Model representing a transcription job."""
    job_id: str
    input_file: Path
    output_file: Optional[Path] = None
    status: str = "pending"  # pending, processing, completed, failed
    model: str
    word_timestamps: bool = False
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None

    model_config = {"arbitrary_types_allowed": True}


class TranscriptionService:
    """Service for handling transcription jobs using MLX Whisper."""
    
    def __init__(self):
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        self._model_path = settings.MODELS_DIR / settings.BATCH_MODEL
        self._model_loaded = False
        self._model = None
        self._jobs: Dict[str, TranscriptionJob] = {}
    
    async def _load_model(self) -> None:
        """Load the MLX Whisper model if not already loaded."""
        if self._model_loaded:
            return
        
        logger.info(f"Loading MLX Whisper model from {self._model_path}")
        
        try:
            # Check if model exists, otherwise try to download it from the Hugging Face Hub
            model_path_or_repo = str(self._model_path)
            if not self._model_path.exists():
                logger.info(f"Model not found locally, attempting to load from 'mlx-community/whisper-{settings.BATCH_MODEL}'")
                model_path_or_repo = f"mlx-community/whisper-{settings.BATCH_MODEL}"
            
            # Load model (use to_thread because model loading is CPU-bound)
            self._model = await asyncio.to_thread(mlx_whisper.load_model, model_path_or_repo)
            self._model_loaded = True
            logger.info(f"MLX Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load MLX Whisper model: {e}")
            raise
    
    async def create_job(
        self,
        input_file: Path,
        word_timestamps: bool = False,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> TranscriptionJob:
        """
        Create a new transcription job.
        
        Args:
            input_file: Path to the input audio file
            word_timestamps: Whether to include word-level timestamps
            language: Optional language code
            prompt: Optional prompt for the model
            temperature: Temperature for sampling
            
        Returns:
            A TranscriptionJob instance
        """
        job_id = generate_unique_id()
        output_file = settings.RESULTS_DIR / f"{job_id}.json"
        
        job = TranscriptionJob(
            job_id=job_id,
            input_file=input_file,
            output_file=output_file,
            status="pending",
            model=settings.BATCH_MODEL,
            word_timestamps=word_timestamps,
            language=language,
            prompt=prompt,
            temperature=temperature,
        )
        
        self._jobs[job_id] = job
        
        # Start processing the job in the background
        asyncio.create_task(self._process_job(job))
        
        return job
    
    async def _process_job(self, job: TranscriptionJob) -> None:
        """
        Process a transcription job.
        
        Args:
            job: The TranscriptionJob instance to process
        """
        # Acquire semaphore to limit concurrent jobs
        async with self._semaphore:
            try:
                # Update job status
                job.status = "processing"
                logger.info(f"Processing job {job.job_id} with file {job.input_file}")
                
                # Ensure model is loaded
                await self._load_model()
                
                # Convert input file to WAV format
                wav_file = await asyncio.to_thread(
                    convert_to_wav, 
                    job.input_file, 
                    settings.UPLOAD_DIR / f"{job.job_id}.wav"
                )
                
                # Transcribe the audio file
                result = await asyncio.to_thread(
                    mlx_whisper.transcribe,
                    str(wav_file),
                    path_or_hf_repo=None,  # Use already loaded model
                    model=self._model,  # Pass the loaded model
                    word_timestamps=job.word_timestamps,
                    language=job.language,
                    prompt=job.prompt,
                    temperature=job.temperature,
                )
                
                # Update job with results
                job.result = result
                job.status = "completed"
                job.completed_at = time.time()
                
                # Save result to file
                async with asyncio.to_thread(
                    open, job.output_file, "w"
                ) as f:
                    await asyncio.to_thread(
                        json.dump, result, f, indent=2
                    )
                
                logger.info(f"Job {job.job_id} completed successfully")
            
            except Exception as e:
                logger.error(f"Error processing job {job.job_id}: {e}")
                job.status = "failed"
                job.error = str(e)
                job.completed_at = time.time()
    
    def get_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """
        Get a transcription job by ID.
        
        Args:
            job_id: The ID of the job to retrieve
            
        Returns:
            The TranscriptionJob instance or None if not found
        """
        return self._jobs.get(job_id)
    
    def list_jobs(self) -> List[TranscriptionJob]:
        """
        List all transcription jobs.
        
        Returns:
            A list of all TranscriptionJob instances
        """
        return list(self._jobs.values())


# Create a global instance of the transcription service
transcription_service = TranscriptionService()
