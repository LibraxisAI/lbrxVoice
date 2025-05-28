"""
Script to run the batch transcription server.
"""
import uvicorn
import os
import asyncio
from pathlib import Path

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger


def main():
    """Run the batch transcription server."""
    logger.info(f"Starting MLX Whisper batch transcription server on port {settings.BATCH_PORT}")
    logger.info(f"Model: {settings.BATCH_MODEL}")
    logger.info(f"Models directory: {settings.MODELS_DIR}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Results directory: {settings.RESULTS_DIR}")
    
    # Ensure directories exist
    os.makedirs(settings.MODELS_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "whisper_servers.batch.api:app",
        host="0.0.0.0",
        port=settings.BATCH_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
