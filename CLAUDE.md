# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
lbrxWhisper implements dual MLX Whisper servers for speech-to-text transcription:
- **Batch Server**: High-quality processing of complete audio files
- **Realtime Server**: Low-latency streaming transcription

## Essential Commands
- **Install**: `uv pip install -e .`
- **Run Batch Server**: `whisper-batch-server` or `python -m whisper_servers batch`
- **Run Realtime Server**: `whisper-realtime-server` or `python -m whisper_servers realtime`
- **Test Client**: `python test_client.py path/to/audio.mp3`
- **WebSocket Client**: `python websocket_client.py --file audio.mp3` or `--microphone`
- **TUI Dashboard**: `python tui_dashboard.py`

## Architecture
The codebase is organized into two main server implementations:
- `whisper_servers/batch/`: FastAPI server for file uploads and batch processing
- `whisper_servers/realtime/`: WebSocket server for streaming audio transcription
- `whisper_servers/common/`: Shared configuration, logging, and utilities
- `mlx_whisper/`: MLX-based Whisper implementation

Both servers use MLX for hardware acceleration and can run different model sizes based on requirements.

## Configuration
Key environment variables:
- `BATCH_PORT` (default: 8123) / `REALTIME_PORT` (default: 8000)
- `BATCH_MODEL` (default: large-v3) / `REALTIME_MODEL` (default: tiny)
- `MODELS_DIR`, `UPLOAD_DIR`, `RESULTS_DIR`
- `MAX_CONCURRENT_JOBS` (default: 2)

## Development Requirements
- Python 3.12+
- FFmpeg for audio processing
- MLX ecosystem (mlx-whisper, mlx-audio)