#!/usr/bin/env python3
"""
🎤 Edge TTS Server - Microsoft Neural Voices
Darmowy, szybki i działający TTS!
"""

import asyncio
import edge_tts
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import tempfile
import os
from pathlib import Path
import uvicorn
from datetime import datetime
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Edge TTS Server", version="1.0.0")

# Dostępne głosy
VOICES = {
    # Polski
    "pl_male": "pl-PL-MarekNeural",
    "pl_female": "pl-PL-ZofiaNeural",
    # English
    "en_male": "en-US-GuyNeural", 
    "en_female": "en-US-JennyNeural",
    "en_aria": "en-US-AriaNeural",
    "en_davis": "en-US-DavisNeural",
    "en_tony": "en-US-TonyNeural",
    "en_sara": "en-US-SaraNeural",
    # Inne języki
    "fr_male": "fr-FR-HenriNeural",
    "de_male": "de-DE-ConradNeural",
    "es_male": "es-ES-AlvaroNeural",
    "it_male": "it-IT-DiegoNeural",
    "ja_female": "ja-JP-NanamiNeural",
    "ko_female": "ko-KR-SunHiNeural",
    "zh_female": "zh-CN-XiaoxiaoNeural"
}

# Style głosu (niektóre głosy wspierają)
STYLES = {
    "normal": None,
    "cheerful": "cheerful",
    "sad": "sad", 
    "angry": "angry",
    "excited": "excited",
    "friendly": "friendly",
    "hopeful": "hopeful",
    "shouting": "shouting",
    "whispering": "whispering",
    "terrified": "terrified",
    "unfriendly": "unfriendly"
}

# Request/Response models
class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: str = Field(default="pl_male", description="Voice ID")
    language: Optional[str] = Field(default="pl", description="Language code")
    speed: Optional[float] = Field(default=1.0, description="Speed (0.5-2.0)")
    pitch: Optional[float] = Field(default=0.0, description="Pitch adjustment in Hz")
    style: Optional[str] = Field(default="normal", description="Voice style")
    output_format: Optional[str] = Field(default="mp3", description="mp3 or wav")

class TTSResponse(BaseModel):
    audio_path: str
    duration: Optional[float] = None
    voice_used: str
    timestamp: str

class VoiceInfo(BaseModel):
    id: str
    name: str
    language: str
    gender: str
    neural: bool = True

# Ścieżka do zapisywania
OUTPUT_DIR = Path("tts_outputs/edge_tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Cache dla głosów
_voices_cache: Optional[List[Dict]] = None
_cache_time: Optional[datetime] = None

async def get_available_voices() -> List[Dict]:
    """Pobierz listę dostępnych głosów z cache"""
    global _voices_cache, _cache_time
    
    # Cache na 1 godzinę
    if _voices_cache and _cache_time:
        if (datetime.now() - _cache_time).seconds < 3600:
            return _voices_cache
    
    voices = await edge_tts.list_voices()
    _voices_cache = voices
    _cache_time = datetime.now()
    return voices

def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """Usuń stare pliki TTS"""
    now = datetime.now()
    for file in directory.glob("*.mp3"):
        if (now - datetime.fromtimestamp(file.stat().st_mtime)).seconds > max_age_hours * 3600:
            try:
                file.unlink()
                logger.info(f"Removed old file: {file}")
            except:
                pass

@app.on_event("startup")
async def startup_event():
    """Inicjalizacja przy starcie"""
    logger.info("🚀 Edge TTS Server starting...")
    
    # Cleanup starych plików
    cleanup_old_files(OUTPUT_DIR)
    
    # Preload voices
    voices = await get_available_voices()
    logger.info(f"✅ Loaded {len(voices)} voices")

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "Edge TTS Server",
        "voices_available": len(VOICES),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/voices", response_model=List[VoiceInfo])
async def list_voices():
    """Lista dostępnych głosów"""
    voices = []
    
    for key, voice_id in VOICES.items():
        lang = key.split("_")[0]
        gender = "male" if "male" in key else "female"
        
        voices.append(VoiceInfo(
            id=key,
            name=voice_id,
            language=lang,
            gender=gender,
            neural=True
        ))
    
    return voices

@app.get("/v1/voices/all")
async def list_all_edge_voices():
    """Lista WSZYSTKICH głosów Edge TTS"""
    voices = await get_available_voices()
    return {
        "total": len(voices),
        "voices": voices
    }

@app.post("/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize(request: TTSRequest, background_tasks: BackgroundTasks):
    """Synteza mowy"""
    try:
        # Wybierz głos
        voice_id = VOICES.get(request.voice, VOICES["pl_male"])
        
        # Przygotuj parametry
        rate = f"{int((request.speed - 1.0) * 100):+d}%"
        pitch = f"{int(request.pitch):+d}Hz"
        
        # Komunikat Edge TTS
        communicate = edge_tts.Communicate(
            text=request.text,
            voice=voice_id,
            rate=rate,
            pitch=pitch
        )
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"edge_{request.voice}_{timestamp}.mp3"
        output_path = OUTPUT_DIR / filename
        
        # Zapisz audio
        await communicate.save(str(output_path))
        
        # Cleanup w tle
        background_tasks.add_task(cleanup_old_files, OUTPUT_DIR, 24)
        
        return TTSResponse(
            audio_path=str(output_path),
            voice_used=voice_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/tts/audio/{filename}")
async def get_audio(filename: str):
    """Pobierz wygenerowany plik audio"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename
    )

@app.post("/v1/tts/preview")
async def preview_voices(text: str = "Cześć! To jest test głosu."):
    """Wygeneruj preview wszystkich głosów"""
    results = []
    
    for voice_key, voice_id in VOICES.items():
        try:
            communicate = edge_tts.Communicate(text, voice_id)
            
            filename = f"preview_{voice_key}.mp3"
            output_path = OUTPUT_DIR / filename
            
            await communicate.save(str(output_path))
            
            results.append({
                "voice": voice_key,
                "voice_id": voice_id,
                "audio_path": str(output_path),
                "url": f"/v1/tts/audio/{filename}"
            })
        except Exception as e:
            results.append({
                "voice": voice_key,
                "error": str(e)
            })
    
    return {"previews": results}

# Uruchom serwer
if __name__ == "__main__":
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8128
    
    print(f"""
    🎤 Edge TTS Server
    ==================
    
    Dostępne endpointy:
    - GET  /                     - Health check
    - GET  /v1/voices           - Lista głosów
    - GET  /v1/voices/all       - Wszystkie głosy Edge
    - POST /v1/tts/synthesize   - Synteza mowy
    - GET  /v1/tts/audio/{file} - Pobierz audio
    - POST /v1/tts/preview      - Preview głosów
    
    Przykład użycia:
    curl -X POST http://localhost:{port}/v1/tts/synthesize \\
         -H "Content-Type: application/json" \\
         -d '{{"text": "Cześć! Jestem Edge TTS!", "voice": "pl_male"}}'
    
    🚀 Serwer startuje na porcie {port}...
    """)
    
    uvicorn.run(
        "edge_tts_server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )