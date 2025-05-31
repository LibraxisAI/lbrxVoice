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
5. **TTS** - Text-to-speech synthesis (XTTS v2)
6. **VoiceAI** - Complete conversational pipeline

### Core Technologies
- **Whisper v3 large**: Speech-to-text on MLX
- **LM Studio API**: Local LLM integration (Qwen3, Llama, etc.)
- **XTTS v2**: Multi-language TTS with Polish support
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
git clone -b lbrxConversational https://github.com/LibraxisAI/lbrxVoice.git
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
# Test all components
uv run python test_components.py

# Test TTS API
uv run python test_tts_api.py

# Test audio recording
uv run python test_audio_recording.py
```

## 👥 Authors

- [Maciej Gad](https://github.com/yourusername) - Veterinarian & AI enthusiast
- [Klaudiusz](https://github.com/anthropics/claude) - AI assistant

---

**No i zajebiście!** 🚀