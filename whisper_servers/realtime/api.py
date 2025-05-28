"""
FastAPI application for the real-time transcription server.
"""
import asyncio
import json
import base64
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from whisper_servers.common.config import settings
from whisper_servers.common.logging import logger
from whisper_servers.realtime.transcription import transcription_service


# Create FastAPI app
app = FastAPI(
    title="MLX Whisper Real-time Transcription API",
    description="API for real-time transcription of audio streams using MLX Whisper",
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


@app.websocket("/v1/audio/transcriptions")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transcription.
    
    The client should send audio data as binary messages or as JSON with a base64-encoded audio field.
    The server will respond with transcription results as JSON.
    """
    await websocket.accept()
    
    try:
        logger.info("WebSocket connection established")
        await transcription_service.transcribe_websocket(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    # Pre-load the model
    try:
        await transcription_service.load_model()
    except Exception as e:
        logger.error(f"Failed to load model on startup: {e}")
