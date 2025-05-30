# TTS → Whisper Pipeline

Complete Text-to-Speech and Speech-to-Text pipeline with multiple TTS backends and MLX optimization.

## 🚀 Features

- **Multiple TTS Backends**:
  - **DIA 1.6B** - High-quality dialogue synthesis with voice cloning
  - **CSM-MLX** - Multi-speaker synthesis with 4 voice options
  
- **Dual Whisper Servers**:
  - Batch processing for complete files
  - Real-time streaming transcription
  
- **MLX Optimized**: Native Apple Silicon acceleration for all models

## 📋 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Text Input    │────▶│   TTS Servers   │────▶│     Audio       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                          │
                        ┌──────┴──────┐                   │
                        │             │                   ▼
                  DIA WebSocket  DIA REST         ┌─────────────────┐
                   (port 8129)  (port 8132)       │ Whisper Servers │
                        │             │            └─────────────────┘
                        │     CSM REST│                   │
                        │    (port 8135)           ┌──────┴──────┐
                        │             │            │             │
                        └─────────────┘        Batch         Realtime
                                            (port 8123)    (port 8126)
                                                  │             │
                                                  ▼             ▼
                                          ┌─────────────────────────┐
                                          │    Transcription        │
                                          └─────────────────────────┘
```

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/LibraxisAI/lbrxWhisper.git
cd lbrxWhisper

# Install with uv
uv pip install -e .

# Convert DIA model to MLX
python dia_mlx_converter.py
```

## 🎯 Quick Start

### 1. Start All Servers
```bash
python start_servers.py
```

This starts:
- Whisper Batch (8123)
- Whisper Realtime (8126)
- DIA WebSocket (8129)
- DIA REST (8132)
- CSM REST (8135)

### 2. Test Pipeline
```bash
# Simple test
python test_pipeline.py

# Full 20-pair test suite
python test_pipeline_polish.py
```

## 📁 Test Outputs

All test results are organized in:
```
test_pipeline/
├── input_texts/       # Original text inputs
├── tts_outputs/       # Generated audio (WAV)
├── whisper_outputs/   # Transcriptions
└── conversations/     # Detailed 1:1 analysis
```

## 🔧 API Examples

### DIA TTS (Dialogue)
```python
# REST API
response = requests.post("http://localhost:8132/synthesize_sync", json={
    "text": "[S1] Hello! [S2] Hi there!",
    "temperature": 0.8
})

# WebSocket (streaming)
ws = websocket.create_connection("ws://localhost:8129/ws/tts")
ws.send(json.dumps({"text": "[S1] Real-time synthesis!"}))
```

### CSM TTS (Multi-speaker)
```python
response = requests.post("http://localhost:8135/synthesize_sync", json={
    "text": "Choose from 4 different voices",
    "speaker_id": "0"  # 0-3
})
```

### Whisper Transcription
```python
# Batch processing
files = {"file": open("audio.wav", "rb")}
response = requests.post("http://localhost:8123/transcribe", 
                        files=files, 
                        data={"language": "pl"})
```

## 🎪 Features

- **Voice Cloning**: DIA supports cloning voices from reference audio
- **Non-verbal sounds**: `(laughs)`, `(sighs)`, `(coughs)` etc.
- **Multiple languages**: Whisper supports 100+ languages
- **Real-time streaming**: WebSocket support for live synthesis

## 🤖 (c)2025 by M&K

---

Built with ❤️ for Apple Silicon using MLX framework