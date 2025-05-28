"""
Script to run the real-time transcription server.
"""
import uvicorn
import os
import asyncio
from pathlib import Path

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger


def main():
    """Run the real-time transcription server."""
    logger.info(f"Starting MLX Whisper real-time transcription server on port {settings.REALTIME_PORT}")
    logger.info(f"Model: {settings.REALTIME_MODEL}")
    logger.info(f"Models directory: {settings.MODELS_DIR}")
    
    # Ensure directories exist
    os.makedirs(settings.MODELS_DIR, exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "whisper_servers.realtime.api:app",
        host="0.0.0.0",
        port=settings.REALTIME_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
