"""
Logging configuration for the MLX Whisper servers.
"""
import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_file: Path = Path("logs/whisper_server.log")):
    """Configure loguru logger with console and file outputs."""
    # Ensure log directory exists
    log_file.parent.mkdir(exist_ok=True, parents=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler for INFO level and above
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler for all levels with rotation
    logger.add(
        log_file,
        rotation="10 MB",
        compression="zip",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    return logger


# Initialize logger
logger = setup_logging()
