# 🚀 lbrxWhisper - Instalacja na świeżym macOS

## Wymagania
- macOS z Apple Silicon (M1/M2/M3)
- Około 20GB miejsca na dysku

## Krok po kroku

### 1. Zainstaluj UV (jeśli nie masz)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Zainstaluj podstawowe narzędzia systemowe
```bash
# Homebrew (jeśli nie masz)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Narzędzia audio
brew install ffmpeg portaudio
```

### 3. Sklonuj i zainstaluj projekt
```bash
# Klonuj repo
git clone https://github.com/YOUR_USERNAME/lbrxWhisper.git
cd lbrxWhisper

# UV sync - to wszystko!
uv sync
```

### 4. Pobierz LM Studio
- Idź na https://lmstudio.ai
- Pobierz i zainstaluj
- Uruchom i pobierz model: **Qwen3-8B** (wersja MLX)
- Kliknij "Start Server" (port 1234)

### 5. Uruchom aplikację
```bash
# Uruchom serwery Whisper + TUI
uv run python run_ultimate_tui.py
```

## Jeśli coś nie działa

### Sprawdź diagnostykę:
```bash
uv run python diagnose.py
```

### Uruchom z logami:
```bash
uv run ./run_with_logs.sh
```

Logi znajdziesz w `logs/session_*.log`

## Nawigacja w TUI
- **F1-F6**: Przełączanie zakładek
- **Tab**: Przechodzenie między elementami  
- **Enter**: Wybór/akcja
- **Ctrl+C**: Wyjście

## FAQ

**P: Błąd "No module named mlx"?**
```bash
uv sync  # UV powinno wszystko zainstalować
```

**P: Mikrofon nie działa?**
- Preferencje Systemowe → Prywatność → Mikrofon
- Zaznacz Terminal/iTerm2
- Zrestartuj terminal

**P: "LM Studio not running"?**
- Uruchom LM Studio
- Załaduj model Qwen3-8B
- Kliknij "Start Server"

---

That's it! UV handles everything else. 🎉