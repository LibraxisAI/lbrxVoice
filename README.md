# MLX Whisper Servers

Dual MLX Whisper servers for real-time and batch speech-to-text transcription.

## Features

- **Batch Transcription Server**:
  - Process pre-recorded audio/video files with the large Whisper-v3 model (3GB)
  - REST API with OpenAI-compatible endpoints
  - Support for ffmpeg-compatible audio/video formats

- **Real-time Transcription Server**:
  - Stream audio transcription in real-time with WebSockets
  - Interactive TUI dashboard with spectrograms and timestamp editing
  - Low-latency processing with a smaller MLX Whisper model

## Setup

### Prerequisites

- Python 3.12 or higher
- FFmpeg installed on your system
- uv package manager

### Installation

```bash
# Create a virtual environment (if not already done)
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

## Usage

### Batch Transcription Server

Start the batch transcription server:

```bash
whisper-batch-server
# or
python -m whisper_servers batch
```

The server will run on port 8123 by default.

### Real-time Transcription Server

Start the real-time transcription server:

```bash
whisper-realtime-server
# or
python -m whisper_servers realtime
```

The server will run on port 8000 by default.

### API Documentation

Once the servers are running, you can access the API documentation at:

- Batch server: http://localhost:8123/docs
- Real-time server: http://localhost:8000/docs

### Testing the Servers

#### Batch Transcription

Use the included test client to transcribe an audio file:

```bash
python test_client.py path/to/audio/file.mp3
```

#### Real-time Transcription

Use the included WebSocket client to stream audio in real-time:

```bash
# Stream from an audio file
python websocket_client.py --file path/to/audio/file.mp3

# Stream from microphone
python websocket_client.py --microphone
```

### TUI Dashboard

A text-based user interface (TUI) dashboard is available for monitoring and managing transcription jobs:

```bash
python tui_dashboard.py
```

## Configuration

Configuration options can be set via environment variables:

- `BATCH_PORT`: Port for batch transcription server (default: 8123)
- `BATCH_MODEL`: Model for batch transcription (default: large-v3)
- `REALTIME_PORT`: Port for real-time transcription server (default: 8000)
- `REALTIME_MODEL`: Model for real-time transcription (default: tiny)
- `MODELS_DIR`: Directory for storing models (default: models/)
- `UPLOAD_DIR`: Directory for uploaded files (default: uploads/)
- `RESULTS_DIR`: Directory for storing results (default: results/)
- `MAX_CONCURRENT_JOBS`: Maximum number of concurrent transcription jobs (default: 2)

## Example API Usage

### Batch Transcription

```python
import requests

url = "http://localhost:8123/v1/audio/transcriptions"
files = {"file": open("audio.mp3", "rb")}
data = {"model": "whisper-large-v3"}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result["text"])
```

### Real-time Transcription

```python
import asyncio
import websockets
import json
import base64

async def transcribe_realtime():
    uri = "ws://localhost:8000/v1/audio/transcriptions"
    async with websockets.connect(uri) as websocket:
        # Read audio chunks and send them
        with open("audio.wav", "rb") as f:
            chunk = f.read(4000)  # 4KB chunks
            while chunk:
                # Send as base64-encoded JSON
                await websocket.send(json.dumps({
                    "audio": base64.b64encode(chunk).decode("utf-8")
                }))
                
                # Receive transcription
                response = await websocket.recv()
                result = json.loads(response)
                print(result["text"])
                
                # Read next chunk
                chunk = f.read(4000)

asyncio.run(transcribe_realtime())
```

## License

This project is licensed under the same license as MLX and MLX Whisper.
