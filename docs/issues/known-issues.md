# Known Issues - lbrxWhisper

## Data: 2025-05-29

### 1. Problem z transkrypcją plików audio przez Whisper Batch Server

**Status:** ❌ Nierozwiązany

**Opis problemu:**
Podczas próby transkrypcji plików audio przez endpoint `/v1/audio/transcriptions` występuje błąd:
```
500: Transcription failed: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'
```

**Kroki reprodukcji:**
1. Uruchomienie serwera: `uv run python -m whisper_servers batch`
2. Wysłanie pliku audio:
```bash
curl -X POST "http://0.0.0.0:8123/v1/audio/transcriptions" \
  -F "file=@/path/to/audio.m4a" \
  -F "language=pl" \
  -F "response_format=json" \
  -F "model=whisper-large-v3-mlx"
```

**Lokalizacja błędu:**
- Plik: `whisper_servers/batch/transcription.py`
- Linia: ~146 (w funkcji `mlx_whisper.transcribe`)
- Problem: Parametr `path_or_hf_repo=None` powoduje błąd typu NoneType

**Logi błędu:**
```
2025-05-29 13:36:08 | ERROR | whisper_servers.batch.transcription:_process_job:170 - Error processing job d157c5e3-8f38-4e37-a0ed-4fab6fcfb4b0: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'
```

**Możliwe rozwiązanie:**
Należy przekazać prawidłową ścieżkę modelu zamiast `None` do funkcji `mlx_whisper.transcribe`.

---

### 2. Problem z nazwą modelu Whisper

**Status:** ✅ Częściowo naprawiony

**Opis problemu:**
Serwer dodawał podwójny prefiks "whisper-" do nazwy modelu, próbując załadować:
- `mlx-community/whisper-whisper-large-v3-mlx` zamiast 
- `mlx-community/whisper-large-v3-mlx`

**Rozwiązanie zastosowane:**
Dodano sprawdzenie czy nazwa modelu już zawiera prefiks "whisper-" w pliku `whisper_servers/batch/transcription.py`:
```python
if settings.BATCH_MODEL.startswith("whisper-"):
    model_repo = f"mlx-community/{settings.BATCH_MODEL}"
else:
    model_repo = f"mlx-community/whisper-{settings.BATCH_MODEL}"
```

---

### 3. Informacje o środowisku

**Działające serwery:**
- Batch Server: http://0.0.0.0:8123 (model: whisper-large-v3-mlx)
- Realtime Server: http://0.0.0.0:8126 (model: medium)

**Testowane pliki audio:**
1. `/Users/maciejgad/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/20250503 103006-7523A0A2.m4a`
2. `/Users/maciejgad/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/20250513 195012.m4a`
3. `/Users/maciejgad/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/20250513 202711-8A913303.m4a`

**Endpointy:**
- Dokumentacja Batch: http://0.0.0.0:8123/docs
- Dokumentacja Realtime: http://0.0.0.0:8126/docs
- Upload (Batch): POST http://0.0.0.0:8123/v1/audio/transcriptions
- WebSocket (Realtime): ws://0.0.0.0:8126/ws

---

### Następne kroki:
1. Naprawić problem z parametrem `path_or_hf_repo` w funkcji transkrypcji
2. Przetestować transkrypcję po naprawie
3. Zapisać wyniki transkrypcji z wszystkich 3 plików audio