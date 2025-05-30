# 🚀 lbrxVoice MVP - Ready for Integration

**Status:** ✅ MVP Ready  
**Data:** 2025-05-30  
**Pipeline:** Audio → ASR → LLM → TTS → Audio

## 📋 Co dostarcza MVP

### 1. **Kompletny pipeline głosowy**
```python
# Prosty w użyciu
from lbrx_voice_pipeline import VoicePipeline

pipeline = VoicePipeline()
results = await pipeline.process_audio("wizyta.m4a")
```

### 2. **Komponenty**

#### ASR (Speech-to-Text)
- ✅ **MLX Whisper** - natywne dla Apple Silicon
- ✅ Optymalizacja dla języka polskiego
- ✅ Zapobieganie powtórzeniom (`condition_on_previous_text=False`)
- ✅ API REST (port 8123) i WebSocket (port 8126)

#### LLM (Analiza tekstu)
- ✅ **Qwen3-8B** przez LM Studio
- ✅ Analiza wizyt weterynaryjnych
- ✅ Ekstrakcja kluczowych informacji
- ✅ Format JSON

#### TTS (Text-to-Speech)
- ✅ **MLX-Audio** z modelami Kokoro/Spark
- ✅ Wsparcie dla języka polskiego
- ✅ Generowanie odpowiedzi głosowych

## 🔌 Endpointy API

### Batch Transcription
```bash
curl -X POST http://localhost:8123/v1/audio/transcriptions \
  -F "file=@audio.m4a" \
  -F "language=pl" \
  -F "response_format=json"
```

### Realtime WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8126/v1/audio/transcriptions');
ws.send(base64AudioData);
```

### LLM Analysis
```bash
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-8b-mlx", "messages": [...]}'
```

## 🏗️ Integracja z Tauri/Vista

### 1. **Backend API**
```typescript
// W Tauri - wywołaj backend
const response = await fetch('http://localhost:8123/v1/audio/transcriptions', {
  method: 'POST',
  body: formData
});
```

### 2. **Streaming**
```typescript
// WebSocket dla real-time
const ws = new WebSocket('ws://localhost:8126/v1/audio/transcriptions');
ws.onmessage = (event) => {
  const transcription = JSON.parse(event.data);
  updateUI(transcription);
};
```

### 3. **Pipeline kompletny**
```typescript
// Lub użyj pipeline endpoint (TODO)
const result = await processVetVisit(audioBlob);
// result = { transcription, analysis, audioResponse }
```

## 🚀 Uruchomienie

### 1. Serwery
```bash
# Terminal 1 - Serwery Whisper
python start_servers.py

# Terminal 2 - LM Studio
# Uruchom LM Studio z modelem qwen3-8b-mlx
```

### 2. Test pipeline
```bash
python lbrx_voice_pipeline.py
```

### 3. Konfiguracja
```bash
# Interaktywny konfigurator
python tools/whisper_config_tui.py
```

## 📊 Przykład wyniku

```json
{
  "transcription": {
    "text": "Pies ma gorączkę 40 stopni, wymiotuje od wczoraj...",
    "language": "pl"
  },
  "analysis": {
    "objawy": ["gorączka 40°C", "wymioty"],
    "diagnoza": "Podejrzenie zatrucia pokarmowego",
    "leczenie": "Płyny dożylne, Cerenia",
    "zalecenia": "Dieta, obserwacja 24h"
  },
  "audio_response": "outputs/response.wav"
}
```

## 🔧 Konfiguracja

### Whisper (ASR)
- Model: `whisper-large-v3-mlx`
- Optymalizacja: Polski preset
- Beam size: 5
- No repetition: `condition_on_previous_text=False`

### LLM
- Model: `qwen3-8b-mlx`
- Endpoint: `http://localhost:1234`
- Temperature: 0.3 (dla spójności)

### TTS
- Model: `kokoro` (multilingual)
- Alternative: `spark` (English)
- Format: WAV 16kHz

## 📁 Struktura projektu

```
lbrxWhisper/
├── lbrx_voice_pipeline.py    # MVP pipeline
├── start_servers.py          # Uruchom serwery
├── tools/
│   ├── whisper_config.py     # Konfiguracja
│   └── whisper_config_tui.py # Konfigurator TUI
├── whisper_servers/          # Serwery API
│   ├── batch/               # REST API
│   └── realtime/            # WebSocket
└── outputs/                 # Wyniki
```

## ⚠️ Znane ograniczenia

1. **TTS** - MLX-Audio w wersji beta, możliwe problemy z polskim
2. **LLM** - Wymaga działającego LM Studio
3. **Pamięć** - ~6GB RAM dla pełnego pipeline

## 🎯 Następne kroki

1. **Docker** - Konteneryzacja dla łatwego deploymentu
2. **Queue** - System kolejkowania dla wielu użytkowników  
3. **Cache** - Buforowanie wyników
4. **Fine-tuning** - Dostosowanie modeli do weterynarii

---

**Gotowe do integracji z Vista!** 🚀

Kontakt: Maciej Gad @ LibraxisAI