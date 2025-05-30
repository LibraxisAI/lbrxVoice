# How to Transcribe Audio with lbrxWhisper

## Server Endpoints

### 1. Batch Transcription Server
- **URL**: `http://0.0.0.0:8123`
- **Endpoint**: `/v1/audio/transcriptions`
- **Method**: POST
- **Model**: whisper-large-v3-mlx

### 2. Realtime WebSocket Server
- **URL**: `ws://0.0.0.0:8126`
- **Endpoint**: `/v1/audio/transcriptions`
- **Protocol**: WebSocket
- **Model**: whisper-medium

## Example Queries

### Batch Transcription (REST API)

#### Basic transcription:
```bash
curl -X POST "http://0.0.0.0:8123/v1/audio/transcriptions" \
  -F "file=@/path/to/your/audio.m4a" \
  -F "response_format=json"
```

#### With language specification:
```bash
curl -X POST "http://0.0.0.0:8123/v1/audio/transcriptions" \
  -F "file=@/path/to/your/audio.m4a" \
  -F "language=pl" \
  -F "response_format=json"
```

#### Response format options:
- `json` - Full JSON with segments and timestamps
- `text` - Plain text only
- `srt` - SRT subtitle format
- `vtt` - WebVTT subtitle format

### Realtime Transcription (WebSocket)

#### Python example:
```python
import asyncio
import websockets
import json
import base64

async def transcribe_realtime():
    uri = "ws://0.0.0.0:8126/v1/audio/transcriptions"
    
    async with websockets.connect(uri) as websocket:
        # For audio file (testing):
        with open("audio.m4a", "rb") as f:
            audio_data = f.read()
        
        message = {
            "type": "audio",
            "data": base64.b64encode(audio_data).decode(),
            "format": "m4a",  # or "mp3", "wav", etc.
            "language": "pl"   # optional
        }
        
        await websocket.send(json.dumps(message))
        
        # Get transcription result
        result = await websocket.recv()
        print(json.loads(result))

# For realtime microphone streaming:
async def stream_microphone():
    uri = "ws://0.0.0.0:8126/v1/audio/transcriptions"
    
    async with websockets.connect(uri) as websocket:
        # Send PCM audio chunks from microphone
        # Format: 16-bit PCM, 16kHz, mono
        
        chunk = get_audio_chunk_from_mic()  # Your mic capture code
        
        message = {
            "type": "audio",
            "data": base64.b64encode(chunk).decode(),
            "format": "pcm",  # Raw PCM for realtime
        }
        
        await websocket.send(json.dumps(message))
        result = await websocket.recv()
        print(json.loads(result))
```

#### JavaScript example:
```javascript
const ws = new WebSocket('ws://0.0.0.0:8126/v1/audio/transcriptions');

ws.onopen = () => {
    // For file upload
    const reader = new FileReader();
    reader.onload = (e) => {
        const base64Audio = btoa(e.target.result);
        ws.send(JSON.stringify({
            type: 'audio',
            data: base64Audio,
            format: 'm4a'
        }));
    };
    reader.readAsBinaryString(audioFile);
};

ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    console.log('Transcription:', result.text);
};
```

## Supported Audio Formats

### Batch Server
- m4a, mp3, wav, flac, ogg, opus, webm
- Any format supported by FFmpeg

### Realtime Server
- **PCM** (16-bit, 16kHz, mono) - for live microphone streaming
- All batch formats for testing/file upload

## Response Format

```json
{
  "task": "transcription",
  "text": "Transcribed text here",
  "language": "pl",
  "duration": 3.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.0,
      "text": "Segment text",
      "tokens": [50364, 316, ...],
      "temperature": 0.0,
      "avg_logprob": -0.5,
      "compression_ratio": 1.2,
      "no_speech_prob": 0.01
    }
  ],
  "words": [
    {
      "word": "word",
      "start": 0.0,
      "end": 0.5,
      "probability": 0.98
    }
  ]
}
```

## Test Audio Files

Example Voice Memos locations on macOS:
```
/Users/<username>/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/
```

## Server Logs

- Batch: `logs/whisper_batch.log`
- Realtime: `logs/whisper_realtime.log`