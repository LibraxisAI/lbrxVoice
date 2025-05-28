"""
WebSocket server for DIA TTS real-time synthesis
"""

import asyncio
import json
import base64
import time
from datetime import datetime
from typing import Optional
import numpy as np
import soundfile as sf
import io

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..common.config import config
from ..common.models import TTSRequest, TTSStreamChunk, TTSError, AudioFormat
from .mlx_model import DiaMLX


app = FastAPI(title="DIA TTS WebSocket Server")

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


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)
        
    async def send_error(self, websocket: WebSocket, error: str, detail: str = None):
        error_msg = TTSError(error=error, detail=detail)
        await websocket.send_json(error_msg.dict())


manager = ConnectionManager()


async def process_tts_stream(websocket: WebSocket, request: TTSRequest):
    """Process TTS request and stream audio chunks"""
    
    start_time = time.time()
    chunk_index = 0
    
    try:
        # Generate audio codes
        audio_codes = dia_model.generate(
            text=request.text,
            temperature=request.temperature or config.temperature,
            top_p=request.top_p or config.top_p
        )
        
        # Convert to audio waveform
        audio_data = dia_model.codes_to_audio(audio_codes, sample_rate=config.sample_rate)
        
        # Split into chunks for streaming (e.g., 0.5 second chunks)
        chunk_size = int(config.sample_rate * 0.5)
        total_chunks = len(audio_data) // chunk_size + (1 if len(audio_data) % chunk_size else 0)
        
        for i in range(total_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(audio_data))
            chunk_audio = audio_data[start_idx:end_idx]
            
            # Convert chunk to requested format
            buffer = io.BytesIO()
            sf.write(buffer, chunk_audio, config.sample_rate, format='WAV')
            buffer.seek(0)
            audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            # Send chunk
            chunk = TTSStreamChunk(
                request_id=request.request_id,
                chunk_index=chunk_index,
                audio_data=audio_base64,
                is_final=(i == total_chunks - 1),
                timestamp=time.time()
            )
            
            await manager.send_json(websocket, chunk.dict())
            chunk_index += 1
            
            # Small delay to simulate real-time streaming
            await asyncio.sleep(0.1)
            
        # Send completion message
        processing_time = time.time() - start_time
        completion_msg = {
            "type": "completion",
            "request_id": request.request_id,
            "total_chunks": chunk_index,
            "duration": len(audio_data) / config.sample_rate,
            "processing_time": processing_time
        }
        await manager.send_json(websocket, completion_msg)
        
    except Exception as e:
        await manager.send_error(websocket, str(e), detail=str(type(e).__name__))


@app.websocket("/ws/tts")
async def websocket_tts_endpoint(websocket: WebSocket):
    """WebSocket endpoint for TTS streaming"""
    
    await manager.connect(websocket)
    print(f"Client connected: {websocket.client}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Parse request
            try:
                if data.get("type") == "ping":
                    await manager.send_json(websocket, {"type": "pong"})
                    continue
                    
                request = TTSRequest(**data)
                print(f"Processing TTS request: {request.request_id}")
                
                # Process in background
                asyncio.create_task(process_tts_stream(websocket, request))
                
            except Exception as e:
                await manager.send_error(websocket, "Invalid request", str(e))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected: {websocket.client}")


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
        "service": "DIA TTS WebSocket Server",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/tts",
            "health": "/health"
        }
    }


def main():
    """Run the WebSocket server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.dia_ws_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()