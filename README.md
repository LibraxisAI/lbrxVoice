# lbrxWhisper

Complete speech processing pipeline with Whisper ASR and TTS models, optimized for Apple Silicon using MLX.

## Features

### Speech Recognition (ASR)
- **Batch Transcription Server**:
  - Process pre-recorded audio/video files with Whisper large-v3 model
  - REST API with OpenAI-compatible endpoints
  - Support for all ffmpeg-compatible audio/video formats

- **Real-time Transcription Server**:
  - Stream audio transcription in real-time with WebSockets
  - Interactive TUI dashboard with spectrograms and timestamp editing
  - Low-latency processing with smaller Whisper models

### Text-to-Speech (TTS)
- **DIA 1.6B TTS**:
  - WebSocket endpoint for real-time streaming synthesis
  - REST API for batch processing and fine-tuning
  - Multi-speaker dialogue support with `[S1]`, `[S2]` tags
  - Non-verbal communications (laughs, coughs, sighs)
  - Voice cloning capabilities

- **CSM-MLX TTS**:
  - REST API endpoint
  - Multiple speaker voices (0-3)
  - Optimized for MLX on Apple Silicon

### AI Conversational Agent
- **Voice Chat with Qwen3-8B**:
  - Real-time voice conversations
  - Speech → Qwen3 → TTS pipeline
  - Support for both DIA and CSM voices

## Setup

### Prerequisites

- Apple Silicon Mac (M1/M2/M3)
- Python 3.12 or higher
- FFmpeg installed on your system
- uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/LibraxisAI/lbrxWhisper.git
cd lbrxWhisper

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

### Download Models

1. **Whisper models** are downloaded automatically on first use
2. **DIA model** conversion:
   ```bash
   python dia_mlx_converter.py
   ```
3. **CSM-MLX** is already available in the system

## Usage

### Starting the Servers

#### Whisper Servers
```bash
# Batch transcription server (port 8123)
whisper-batch-server

# Real-time transcription server (port 8000)
whisper-realtime-server
```

#### TTS Servers
```bash
# DIA WebSocket server (port 8124)
python -m tts_servers dia-ws

# DIA REST API (port 8125)
python -m tts_servers dia-rest

# CSM REST API (port 8126)
python -m tts_servers csm-rest
```

### API Documentation

Once running, access the API documentation at:
- Whisper Batch: http://localhost:8123/docs
- Whisper Real-time: http://localhost:8000/docs
- DIA REST: http://localhost:8125/docs
- CSM REST: http://localhost:8126/docs

### Testing the Pipeline

#### Full Pipeline Test
```bash
python test_tts_pipeline.py
```

#### Conversational AI
```bash
python conversational_agent.py
```

#### Real-time Voice Chat
```bash
python voice_chat_realtime.py
```

### Example API Usage

#### TTS Generation (DIA)
```python
import requests

# Synchronous generation
response = requests.post(
    "http://localhost:8125/synthesize_sync",
    json={
        "text": "[S1] Hello from DIA! [S2] This is amazing.",
        "temperature": 0.8
    }
)
audio_base64 = response.json()["audio_data"]
```

#### TTS Generation (CSM)
```python
# With speaker selection
response = requests.post(
    "http://localhost:8126/synthesize_sync",
    json={
        "text": "Hello from CSM model!",
        "speaker_id": "1"  # Choose speaker 0-3
    }
)
```

#### Full Voice Pipeline
```python
from test_tts_pipeline import TTSPipelineTester

tester = TTSPipelineTester()
# Generate speech
audio = tester.test_dia_rest("Hello world!")
# Transcribe it back
text = tester.test_whisper_batch(audio, "test.wav")
```

## Configuration

Environment variables:
- `BATCH_PORT`: Whisper batch port (default: 8123)
- `REALTIME_PORT`: Whisper realtime port (default: 8000)
- `DIA_WS_PORT`: DIA WebSocket port (default: 8124)
- `DIA_REST_PORT`: DIA REST port (default: 8125)
- `CSM_REST_PORT`: CSM REST port (default: 8126)
- `MODELS_DIR`: Model storage directory
- `HF_TOKEN`: Hugging Face token for model downloads

## Project Structure

```
lbrxWhisper/
├── whisper_servers/     # ASR servers
│   ├── batch/          # Batch transcription
│   └── realtime/       # Real-time streaming
├── tts_servers/        # TTS servers
│   ├── dia/           # DIA 1.6B implementation
│   ├── csm/           # CSM-MLX wrapper
│   └── common/        # Shared utilities
├── mlx_whisper/        # Core Whisper MLX
├── conversational_agent.py  # AI chat with voice
├── voice_chat_realtime.py   # Real-time voice loop
└── test_tts_pipeline.py     # Integration tests
```

## Performance

On M3 Max (48GB RAM):
- Full pipeline uses ~20-25GB RAM
- Whisper large-v3: ~3-4GB
- DIA 1.6B: ~6-7GB
- CSM 1B: ~4GB
- Qwen3-8B-Q4: ~6-8GB

## License

Licensed under Apache 2.0. See LICENSE file for details.

## Acknowledgments

- [MLX](https://github.com/ml-explore/mlx) by Apple
- [DIA](https://github.com/nari-labs/dia) by Nari Labs
- [CSM](https://github.com/senstella/csm-mlx) by Senstella
- [Whisper](https://github.com/openai/whisper) by OpenAI