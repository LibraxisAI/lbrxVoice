"""
Utility functions for the MLX Whisper servers.
"""
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO

import ffmpeg
import aiofiles
from fastapi import UploadFile

from whisper_servers.common.logging import logger
from whisper_servers.common.config import settings


async def save_upload_file(upload_file: UploadFile, destination: Optional[Path] = None) -> Path:
    """
    Save an uploaded file to disk.
    
    Args:
        upload_file: The uploaded file
        destination: Optional destination path; if not provided, will use a random name in the upload directory
        
    Returns:
        Path to the saved file
    """
    if destination is None:
        # Create a unique filename
        ext = get_file_extension(upload_file.filename or "")
        filename = f"{uuid.uuid4()}{ext}"
        destination = settings.UPLOAD_DIR / filename
    
    async with aiofiles.open(destination, "wb") as out_file:
        # Read chunks to avoid loading large files into memory
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)
    
    logger.info(f"Saved uploaded file to {destination}")
    return destination


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: The filename to extract extension from
        
    Returns:
        The file extension including the dot (e.g., '.mp3')
    """
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".bin"  # Default extension if none is provided
    return ext


def convert_to_wav(input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None) -> Path:
    """
    Convert any audio file to WAV format using ffmpeg.
    
    Args:
        input_file: Path to the input audio file
        output_file: Optional path for the output WAV file
        
    Returns:
        Path to the converted WAV file
    """
    input_file = Path(input_file)
    
    # If no output file is specified, create one in the same directory
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}.wav"
    
    output_file = Path(output_file)
    
    try:
        # Use ffmpeg to convert the file
        (
            ffmpeg
            .input(str(input_file))
            .output(str(output_file), acodec="pcm_s16le", ar="16000", ac=1)
            .run(quiet=True, overwrite_output=True)
        )
        logger.info(f"Converted {input_file} to WAV format at {output_file}")
        return output_file
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise RuntimeError(f"Failed to convert audio file: {e}")


def is_audio_file(filename: str) -> bool:
    """
    Check if a file is a supported audio format.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if the file extension is in the supported formats, False otherwise
    """
    ext = get_file_extension(filename).lower().lstrip(".")
    return ext in settings.SUPPORTED_FORMATS


def generate_unique_id() -> str:
    """
    Generate a unique ID for a transcription job.
    
    Returns:
        A unique ID string
    """
    return str(uuid.uuid4())
