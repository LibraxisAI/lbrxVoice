# lbrxVoice - 6-Tab Voice AI Platform

## 🚀 Quick Install (macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/LibraxisAI/lbrxVoice/main/install.sh | sh
```

That's it! The installer will:
- ✅ Install UV package manager
- ✅ Clone the repository to `~/lbrxVoice`
- ✅ Install all dependencies
- ✅ Create `lbrxvoice` command

## 🎯 Features

### 6-Tab Terminal UI
1. **Chat** - LM Studio integration with streaming responses
2. **RAG** - Vector search knowledge base with ChromaDB
3. **Files** - Batch transcription with semantic naming
4. **Voice** - Live transcription with audio spectrogram
5. **TTS** - Text-to-speech synthesis (Microsoft Edge TTS)
6. **VoiceAI** - Complete conversational pipeline

### Core Technologies
- **Whisper v3 large**: Speech-to-text on MLX
- **LM Studio API**: Local LLM integration (Qwen3, Llama, etc.)
- **Microsoft Edge TTS**: High-quality neural voices (12+ languages, Polish included)
- **ChromaDB**: Vector database for RAG
- **MLX Framework**: Apple Silicon optimization

## 🏃 Running

After installation:
```bash
lbrxvoice
```

Or manually:
```bash
cd ~/lbrxVoice
uv run python run_ultimate_tui.py
```

## Navigation
- **F1-F6**: Switch between tabs
- **Tab**: Navigate elements
- **Enter**: Select/Send
- **Ctrl+C**: Exit

## 🎤 Text-to-Speech (Edge TTS)

lbrxVoice uses **Microsoft Edge TTS** for high-quality speech synthesis:

### ✅ Why Edge TTS?
- **Free**: No API keys or registration required
- **High Quality**: Neural voices that sound natural
- **Multi-language**: Polish, English, German, French, Spanish, Italian, Japanese, Korean, Chinese
- **Fast**: Instant synthesis without GPU requirements
- **Reliable**: Actually works (unlike our other TTS attempts!)

### Available Voices
- **Polish**: Marek (male), Zofia (female) 
- **English**: Guy, Jenny, Aria, Davis, Tony, Sara
- **Other languages**: French Henri, German Conrad, Spanish Alvaro, etc.

### Voice Controls
- **Speed**: 0.5x to 2.0x (normal = 1.0x)
- **Pitch**: -25Hz to +25Hz (normal = 0Hz)
- **Styles**: Normal, cheerful, sad, angry, excited, friendly

### Testing TTS
```bash
# Start Edge TTS server
uv run python tts_servers/edge_tts_server.py

# Test synthesis
uv run python test_edge_tts.py
```

## 🐉 Using Dragon (512GB M3 Ultra)

Connect to Dragon via Tailscale:
```bash
cd ~/lbrxVoice
./use_dragon.sh
```

Or manually set in `.env`:
```
LLM_ENDPOINT=http://100.82.232.70:1234/v1/chat/completions
```

## 📋 Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.11 (managed by UV)
- FFmpeg: `brew install ffmpeg`
- LM Studio: https://lmstudio.ai

## 🛠️ Manual Installation

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/LibraxisAI/lbrxVoice.git
cd lbrxVoice
uv sync

# Run
uv run python run_ultimate_tui.py
```

## 📁 Project Structure

```
lbrxVoice/
├── whisper_servers/     # ASR servers (batch & realtime)
├── tts_servers/         # TTS implementations
├── lbrxchat/           # 6-tab TUI application
│   └── tabs/           # Individual tab implementations
├── rag/                # RAG system with ChromaDB
├── audio/              # Audio recording/playback
└── config/             # LLM endpoint configuration
```

## 🔧 Configuration

Create `.env` file:
```env
# LLM Settings
LLM_ENDPOINT=http://localhost:1234/v1/chat/completions
LLM_MODEL=qwen3-8b-mlx

# For OpenRouter
# LLM_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
# OPENROUTER_API_KEY=your-key-here
```

## 📖 Documentation

- [FRESH_INSTALL.md](FRESH_INSTALL.md) - Detailed setup guide
- [HOW-TO-INSTALL.md](HOW-TO-INSTALL.md) - Step-by-step instructions
- [UV_INSTALL.md](UV_INSTALL.md) - UV package manager guide

## 🧪 Testing

```bash
# Quick component check
uv run python test_components.py

# Complete system test (auto-starts servers)
uv run python test_complete_system.py

# Edge TTS integration test (comprehensive)
uv run python test_edge_tts_integration.py

# Individual tests
uv run python test_edge_tts.py         # Basic Edge TTS
uv run python test_audio_recording.py  # Audio devices

# Start all servers manually
uv run python start_servers.py
```

### Expected Test Results ✅
- **Whisper**: Batch and realtime ASR working
- **LM Studio**: Chat with streaming responses  
- **Edge TTS**: Multiple voices and languages
- **MLX**: Apple Silicon optimization active
- **Audio**: Multiple input devices detected

## 👥 Authors

- [Monika Szymanska](https://github.com/m-szymanska) - Veterinarian & Data Scientist
- [Klaudiusz](https://github.com/anthropics/claude) - AI Developer & Coding Genius

---

**No i zajebiście!** 🚀