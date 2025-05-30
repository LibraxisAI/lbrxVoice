# lbrxWhisper Project Structure

## Overview
This document describes the organization of the lbrxWhisper project after restructuring according to best practices.

## Directory Structure

```
lbrxWhisper/
├── docs/                    # Documentation files
│   ├── PROJECT_STATUS.md    # Current project status
│   ├── TTS_PIPELINE_README.md # TTS pipeline documentation
│   ├── WHISPER_CONFIG_ANALYSIS.md # Whisper configuration analysis
│   ├── how_to_transcribe.md # Transcription guide
│   └── issues/              # Known issues documentation
├── examples/                # Example scripts and demos
│   ├── conversational_agent.py # Conversational AI example
│   ├── hello.py             # Simple hello world example
│   ├── lbrx_whisper_demo.py # Main demo script
│   ├── test_optimized_transcription.py # Optimization testing
│   ├── voice_chat_realtime.py # Real-time voice chat example
│   └── websocket_client.py # WebSocket client example
├── logs/                    # Log files (auto-generated)
├── mlx_whisper/            # Core MLX Whisper implementation
│   ├── assets/             # Model assets and tokenizers
│   ├── audio.py            # Audio processing
│   ├── cli.py              # Command-line interface
│   ├── decoding.py         # Decoding logic
│   ├── load_models.py      # Model loading utilities
│   ├── tokenizer.py        # Tokenizer implementation
│   ├── transcribe.py       # Transcription core
│   └── whisper.py          # Main Whisper model
├── models/                 # Downloaded and converted models
│   ├── dia/                # DIA model files
│   ├── dia_cache/          # DIA model cache
│   └── dia_mlx/            # MLX-converted DIA model
├── output/                 # Generated output files
├── outputs/                # Transcription outputs
│   ├── txt/                # English transcriptions
│   └── txt_pl/             # Polish transcriptions
├── results/                # JSON result files
├── scripts/                # Batch processing scripts
│   ├── batch_transcribe_all.py # Transcribe all files
│   ├── batch_transcribe_polish.py # Polish batch transcription
│   ├── batch_transcribe_remaining.py # Process remaining files
│   └── transcribe_polish.py # Single Polish file transcription
├── test_pipeline/          # Testing scripts and guides
│   ├── conversations/      # Conversation test data
│   ├── tts_outputs/        # TTS test outputs
│   └── whisper_outputs/    # Whisper test outputs
├── tools/                  # Utility tools
│   ├── benchmark.py        # Performance benchmarking
│   ├── check_results.py    # Result verification
│   ├── convert.py          # Model conversion tool
│   ├── convert-to-mlx.sh   # MLX conversion script
│   ├── dia_mlx_converter.py # DIA to MLX converter
│   ├── dia_to_mlx_converter.py # Alternative DIA converter
│   ├── list_results_api.py # List API results
│   ├── tui_dashboard.py    # Terminal UI dashboard
│   ├── tui_whisper_config.py # TUI configuration
│   ├── upload_to_hf.py     # HuggingFace upload tool
│   ├── whisper_config.py   # Whisper configuration
│   └── whisper_config_tui.py # Alternative config TUI
├── tts_outputs/            # TTS generation outputs
├── tts_servers/            # TTS server implementations
│   ├── common/             # Common TTS utilities
│   ├── csm/                # CSM TTS server
│   └── dia/                # DIA TTS server
├── tts_temp/               # Temporary TTS files
├── uploads/                # Uploaded audio files
├── whisper_servers/        # Whisper server implementations
│   ├── batch/              # Batch processing server
│   ├── common/             # Common server utilities
│   └── realtime/           # Real-time processing server
├── main.py                 # Main entry point
├── start_servers.py        # Server startup script
├── setup.py                # Package setup
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
├── uv.lock                 # UV lock file
├── README.md               # Main README
└── README_pl.md            # Polish README
```

## Key Components

### Core Library (`mlx_whisper/`)
The main MLX-based Whisper implementation optimized for Apple Silicon.

### Servers
- **whisper_servers/**: HTTP and WebSocket servers for transcription
- **tts_servers/**: Text-to-speech servers (DIA and CSM)

### Scripts
- **scripts/**: Batch processing scripts for transcribing multiple files
- **tools/**: Utility scripts for conversion, benchmarking, and configuration
- **examples/**: Example implementations and demos

### Data Directories
- **uploads/**: Input audio files for processing
- **outputs/**: Transcription text outputs
- **results/**: JSON metadata and results
- **models/**: Downloaded and converted model files
- **logs/**: Server and processing logs

## Usage

### Running Servers
```bash
python start_servers.py
```

### Batch Transcription
```bash
python scripts/batch_transcribe_all.py
python scripts/batch_transcribe_polish.py
```

### Tools
```bash
python tools/benchmark.py
python tools/convert.py --model-path <path>
python tools/tui_dashboard.py
```

### Examples
```bash
python examples/lbrx_whisper_demo.py
python examples/voice_chat_realtime.py
```