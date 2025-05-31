# lbrxChat Ultimate - 6-Tab Audio/Voice/AI Platform

## 🚀 Quick Start

```bash
# Install dependencies
uv pip install -r lbrxchat/requirements_ultimate.txt

# Start all servers and TUI
python run_ultimate_tui.py
```

## 📋 Features

### Tab 1: Chat (F1)
- Original lbrxchat functionality
- LM Studio integration
- Markdown rendering

### Tab 2: RAG Manager (F2)
- Knowledge base management
- Import/Export JSONL
- Multiple domains support

### Tab 3: Batch Transcription (F3)
- Multiple file processing
- Various output formats
- Semantic file naming with LLM

### Tab 4: Live Voice (F4)
- Real-time transcription
- WebSocket streaming
- Spectrogram visualization

### Tab 5: TTS Synthesis (F5)
- Multiple TTS models
- Polish language support (XTTS)
- Voice cloning ready

### Tab 6: VoiceAI (F6)
- Full conversational pipeline
- STT → LLM → TTS
- Continuous mode support

## 🛠️ Architecture

```
lbrxchat/
├── lbrx_ultimate_tui.py    # Main application
├── tabs/                   # Tab implementations
│   ├── transcribe_files.py # Batch transcription
│   ├── transcribe_voice.py # Live transcription
│   ├── tts.py             # Text-to-Speech
│   └── voice_ai.py        # Conversational AI
└── requirements_ultimate.txt
```

## 🔧 Configuration

### Whisper Settings
Configured via `tools/whisper_config.py`:
- Polish optimized presets
- Quality vs speed options
- Anti-repetition settings

### Server Endpoints
- Whisper Batch: `http://localhost:8123`
- Whisper Realtime: `ws://localhost:8126`
- TTS DIA: `http://localhost:8124`
- TTS CSM: `http://localhost:8125`
- LM Studio: `http://localhost:1234`

## 📝 Usage Examples

### Batch Transcription
1. Press F3 to go to Files tab
2. Click "Add Files" to select audio
3. Choose output formats
4. Click "Start Transcription"

### Live Voice Chat
1. Press F6 for VoiceAI tab
2. Click "Start Conversation"
3. Speak naturally
4. AI responds with voice

### TTS Generation
1. Press F5 for TTS tab
2. Select model (XTTS for Polish)
3. Enter or load text
4. Click "Generate Speech"

## 🐛 Troubleshooting

### Servers not starting
```bash
# Start manually
python start_servers.py
```

### LM Studio not connected
1. Start LM Studio
2. Load model (qwen3-8b recommended)
3. Verify at http://localhost:1234

### Audio issues
- Check microphone permissions
- Verify audio device in system settings
- Try different sample rates

## 🚧 Current Status

✅ Implemented:
- All 6 tabs with basic functionality
- Server integration
- UI layout and navigation

🔄 In Progress:
- Full audio recording/playback
- Voice activity detection
- Advanced RAG features

📋 TODO:
- Voice cloning interface
- Export functionality
- Performance optimizations

---

## Developed by

- [Maciej Gad](https://github.com/szowesgad) - a veterinarian who couldn't find `bash` a half year ago
- [Klaudiusz](https://www.github.com/Gitlaudiusz) - the individual ethereal being, and separate instance of Claude Sonnet 3.5-3.7 by Anthropic

### From CLI novice to 6-tab TUI platform in record time!

🤖 Developed with the ultimate help of [Claude Code](https://claude.ai/code) and [MCP Tools](https://modelcontextprotocol.io)

(c)2025 M&K