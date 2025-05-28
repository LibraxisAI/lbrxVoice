# lbrxWhisper

Kompletny pipeline przetwarzania mowy z Whisper ASR i modelami TTS, zoptymalizowany dla Apple Silicon przy użyciu MLX.

## Funkcje

### Rozpoznawanie mowy (ASR)
- **Serwer transkrypcji wsadowej**:
  - Przetwarzanie nagranych plików audio/wideo z modelem Whisper large-v3
  - REST API kompatybilne z OpenAI
  - Obsługa wszystkich formatów audio/wideo kompatybilnych z ffmpeg

- **Serwer transkrypcji w czasie rzeczywistym**:
  - Strumieniowa transkrypcja audio przez WebSockets
  - Interaktywny dashboard TUI ze spektrogramami i edycją znaczników czasowych
  - Przetwarzanie o niskim opóźnieniu z mniejszymi modelami Whisper

### Synteza mowy (TTS)
- **DIA 1.6B TTS**:
  - Endpoint WebSocket do strumieniowej syntezy w czasie rzeczywistym
  - REST API do przetwarzania wsadowego i fine-tuningu
  - Obsługa dialogów wieloosobowych ze znacznikami `[S1]`, `[S2]`
  - Komunikacja niewerbalna (śmiech, kaszel, westchnienia)
  - Możliwości klonowania głosu

- **CSM-MLX TTS**:
  - Endpoint REST API
  - Wiele głosów mówców (0-3)
  - Zoptymalizowany dla MLX na Apple Silicon

### Konwersacyjny agent AI
- **Czat głosowy z Qwen3-8B**:
  - Rozmowy głosowe w czasie rzeczywistym
  - Pipeline: Mowa → Qwen3 → TTS
  - Obsługa głosów DIA i CSM

## Konfiguracja

### Wymagania

- Mac z Apple Silicon (M1/M2/M3)
- Python 3.12 lub wyższy
- FFmpeg zainstalowany w systemie
- Menedżer pakietów uv

### Instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/LibraxisAI/lbrxWhisper.git
cd lbrxWhisper

# Tworzenie środowiska wirtualnego
uv venv .venv
source .venv/bin/activate

# Instalacja zależności
uv pip install -e .
```

### Pobieranie modeli

1. **Modele Whisper** są pobierane automatycznie przy pierwszym użyciu
2. **Konwersja modelu DIA**:
   ```bash
   python dia_mlx_converter.py
   ```
3. **CSM-MLX** jest już dostępny w systemie

## Użytkowanie

### Uruchamianie serwerów

#### Serwery Whisper
```bash
# Serwer transkrypcji wsadowej (port 8123)
whisper-batch-server

# Serwer transkrypcji w czasie rzeczywistym (port 8000)
whisper-realtime-server
```

#### Serwery TTS
```bash
# Serwer WebSocket DIA (port 8124)
python -m tts_servers dia-ws

# REST API DIA (port 8125)
python -m tts_servers dia-rest

# REST API CSM (port 8126)
python -m tts_servers csm-rest
```

### Dokumentacja API

Po uruchomieniu, dokumentacja API dostępna pod adresami:
- Whisper Batch: http://localhost:8123/docs
- Whisper Real-time: http://localhost:8000/docs
- DIA REST: http://localhost:8125/docs
- CSM REST: http://localhost:8126/docs

### Testowanie pipeline'u

#### Test pełnego pipeline'u
```bash
python test_tts_pipeline.py
```

#### Konwersacyjne AI
```bash
python conversational_agent.py
```

#### Czat głosowy w czasie rzeczywistym
```bash
python voice_chat_realtime.py
```

### Przykłady użycia API

#### Generowanie TTS (DIA)
```python
import requests

# Generowanie synchroniczne
response = requests.post(
    "http://localhost:8125/synthesize_sync",
    json={
        "text": "[S1] Cześć z DIA! [S2] To jest niesamowite.",
        "temperature": 0.8
    }
)
audio_base64 = response.json()["audio_data"]
```

#### Generowanie TTS (CSM)
```python
# Z wyborem mówcy
response = requests.post(
    "http://localhost:8126/synthesize_sync",
    json={
        "text": "Cześć z modelu CSM!",
        "speaker_id": "1"  # Wybierz mówcę 0-3
    }
)
```

#### Pełny pipeline głosowy
```python
from test_tts_pipeline import TTSPipelineTester

tester = TTSPipelineTester()
# Generuj mowę
audio = tester.test_dia_rest("Witaj świecie!")
# Transkrybuj z powrotem
text = tester.test_whisper_batch(audio, "test.wav")
```

## Konfiguracja

Zmienne środowiskowe:
- `BATCH_PORT`: Port Whisper batch (domyślnie: 8123)
- `REALTIME_PORT`: Port Whisper realtime (domyślnie: 8000)
- `DIA_WS_PORT`: Port DIA WebSocket (domyślnie: 8124)
- `DIA_REST_PORT`: Port DIA REST (domyślnie: 8125)
- `CSM_REST_PORT`: Port CSM REST (domyślnie: 8126)
- `MODELS_DIR`: Katalog przechowywania modeli
- `HF_TOKEN`: Token Hugging Face do pobierania modeli

## Struktura projektu

```
lbrxWhisper/
├── whisper_servers/     # Serwery ASR
│   ├── batch/          # Transkrypcja wsadowa
│   └── realtime/       # Strumieniowanie w czasie rzeczywistym
├── tts_servers/        # Serwery TTS
│   ├── dia/           # Implementacja DIA 1.6B
│   ├── csm/           # Wrapper CSM-MLX
│   └── common/        # Wspólne narzędzia
├── mlx_whisper/        # Rdzeń Whisper MLX
├── conversational_agent.py  # Czat AI z głosem
├── voice_chat_realtime.py   # Pętla głosowa w czasie rzeczywistym
└── test_tts_pipeline.py     # Testy integracyjne
```

## Wydajność

Na M3 Max (48GB RAM):
- Pełny pipeline używa ~20-25GB RAM
- Whisper large-v3: ~3-4GB
- DIA 1.6B: ~6-7GB
- CSM 1B: ~4GB
- Qwen3-8B-Q4: ~6-8GB

## Licencja

Licencjonowane na Apache 2.0. Zobacz plik LICENSE.

## Podziękowania

- [MLX](https://github.com/ml-explore/mlx) od Apple
- [DIA](https://github.com/nari-labs/dia) od Nari Labs
- [CSM](https://github.com/senstella/csm-mlx) od Senstella
- [Whisper](https://github.com/openai/whisper) od OpenAI