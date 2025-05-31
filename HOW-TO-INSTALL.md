# 🚀 Kompletny Przewodnik Instalacji lbrxWhisper & lbrxChat Ultimate

## Spis Treści
1. [Szybki Start (dla niecierpliwych)](#szybki-start)
2. [Wymagania Systemowe](#wymagania-systemowe)
3. [Instalacja Krok po Kroku](#instalacja-krok-po-kroku)
4. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)
5. [Pierwsze Uruchomienie](#pierwsze-uruchomienie)
6. [FAQ - Najczęstsze Pytania](#faq)

---

## 🎯 Szybki Start

Jeśli masz już wszystko zainstalowane, wykonaj:

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/LibraxisAI/lbrxVoice.git
cd lbrxVoice

# 2. Zainstaluj zależności
uv pip install -r requirements.txt

# 3. Uruchom serwery
python start_servers.py

# 4. W nowym terminalu - uruchom TUI
python run_ultimate_tui.py
```

Jeśli coś nie działa - czytaj dalej! 👇

---

## 💻 Wymagania Systemowe

### Minimalne:
- **System**: macOS 12+ (Monterey lub nowszy) z Apple Silicon (M1/M2/M3)
- **RAM**: 16 GB
- **Dysk**: 20 GB wolnego miejsca
- **Python**: 3.11 lub 3.10 (NIE 3.12!)

### Zalecane:
- **System**: macOS 14+ (Sonoma)
- **RAM**: 32 GB lub więcej
- **Procesor**: M2 Pro/Max lub M3

### Sprawdź swoją konfigurację:
```bash
# Sprawdź wersję macOS
sw_vers

# Sprawdź procesor
sysctl -n machdep.cpu.brand_string

# Sprawdź RAM
system_profiler SPHardwareDataType | grep Memory

# Sprawdź Python
python3 --version
```

---

## 📦 Instalacja Krok po Kroku

### Krok 1: Przygotowanie Systemu

#### 1.1 Zainstaluj Homebrew (jeśli nie masz)
```bash
# Sprawdź czy masz Homebrew
brew --version

# Jeśli nie masz, zainstaluj:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Dodaj do PATH (dla Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

#### 1.2 Zainstaluj podstawowe narzędzia
```bash
# Git (do pobierania kodu)
brew install git

# FFmpeg (do przetwarzania audio)
brew install ffmpeg

# PortAudio (do nagrywania dźwięku)
brew install portaudio

# Sox (opcjonalne, do edycji audio)
brew install sox
```

### Krok 2: Instalacja Pythona

#### ⚠️ WAŻNE: Python 3.12 NIE jest wspierany przez TTS!

#### Opcja A: Przez Homebrew (zalecane)
```bash
# Zainstaluj Python 3.11
brew install python@3.11

# Ustaw jako domyślny
brew link python@3.11

# Sprawdź
python3.11 --version
```

#### Opcja B: Przez pyenv
```bash
# Zainstaluj pyenv
brew install pyenv

# Dodaj do ~/.zshrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Zainstaluj Python 3.11
pyenv install 3.11.8
pyenv global 3.11.8

# Sprawdź
python --version
```

### Krok 3: Instalacja UV (menedżer pakietów)

```bash
# Instalacja UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Lub przez pip
pip install uv

# Sprawdź
uv --version
```

### Krok 4: Pobierz kod projektu

```bash
# Utwórz folder na projekty (jeśli nie masz)
mkdir -p ~/Projects
cd ~/Projects

# Sklonuj repozytorium
git clone https://github.com/LibraxisAI/lbrxVoice.git

# Wejdź do folderu
cd lbrxVoice

# Przełącz na branch z TUI
git checkout lbrxConversational
```

### Krok 5: Utwórz środowisko wirtualne

```bash
# Utwórz venv z Python 3.11
python3.11 -m venv venv

# Aktywuj środowisko
source venv/bin/activate

# Sprawdź że używasz właściwego Pythona
which python
# Powinno pokazać: /Users/TWOJA_NAZWA/Projects/lbrxVoice/venv/bin/python
```

### Krok 6: Zainstaluj zależności

```bash
# Podstawowe zależności
uv pip install -r requirements.txt

# Jeśli UV nie działa, użyj zwykłego pip:
pip install -r requirements.txt

# Dodatkowe zależności dla TUI
uv pip install -r lbrxchat/requirements_ultimate.txt
```

#### Rozwiązywanie problemów z zależnościami:

**Problem: "No module named '_tkinter'"**
```bash
brew install python-tk@3.11
```

**Problem: "error: Microsoft Visual C++ 14.0 is required"** (nie dotyczy macOS)
```bash
# Na macOS zainstaluj Xcode Command Line Tools
xcode-select --install
```

**Problem z PyAudio**
```bash
# Najpierw upewnij się że masz portaudio
brew install portaudio

# Potem instaluj PyAudio ze wskazaniem ścieżek
pip install --global-option='build_ext' --global-option='-I/opt/homebrew/include' --global-option='-L/opt/homebrew/lib' pyaudio
```

### Krok 7: Zainstaluj LM Studio

LM Studio to aplikacja do uruchamiania modeli językowych lokalnie.

1. Pobierz LM Studio: https://lmstudio.ai/
2. Zainstaluj aplikację (przeciągnij do Applications)
3. Uruchom LM Studio
4. Pobierz model **Qwen3-8B**:
   - Kliknij "Browse Models"
   - Wyszukaj "qwen3-8b"
   - Wybierz wersję MLX (dla Apple Silicon)
   - Kliknij "Download"
   - Poczekaj na pobranie (około 8GB)
5. Po pobraniu, kliknij "Load Model"
6. Kliknij "Start Server" (domyślnie na porcie 1234)

### Krok 8: Pobierz modele Whisper

```bash
# Uruchom Python i pobierz model
python -c "
import mlx_whisper
print('Pobieram model Whisper Large v3...')
# Model pobierze się automatycznie przy pierwszym użyciu
"

# Alternatywnie, pobierz ręcznie
mkdir -p ~/.cache/whisper
cd ~/.cache/whisper
# Tutaj możesz pobrać modele ręcznie jeśli potrzeba
```

---

## 🚀 Pierwsze Uruchomienie

### 1. Uruchom serwery Whisper

```bash
# W pierwszym terminalu
cd ~/Projects/lbrxVoice
source venv/bin/activate
python start_servers.py
```

Powinieneś zobaczyć:
```
Starting whisper servers...
Batch server running on http://localhost:8123
Realtime server running on ws://localhost:8126
```

### 2. Sprawdź czy LM Studio działa

Otwórz przeglądarkę i wejdź na: http://localhost:1234/v1/models

Powinieneś zobaczyć listę załadowanych modeli.

### 3. Uruchom TUI (w nowym terminalu)

```bash
# Otwórz nowy terminal (Cmd+T)
cd ~/Projects/lbrxVoice
source venv/bin/activate
python run_ultimate_tui.py
```

### 4. Nawigacja w TUI

- **F1-F6**: Przełączanie między zakładkami
- **Tab**: Przechodzenie między elementami
- **Enter**: Wybór/akcja
- **Ctrl+C**: Wyjście

---

## 🔧 Rozwiązywanie Problemów

### Problem: "Permission denied" przy nagrywaniu

**macOS wymaga uprawnień do mikrofonu:**

1. Otwórz Preferencje Systemowe → Prywatność i bezpieczeństwo → Mikrofon
2. Znajdź Terminal (lub iTerm2) i zaznacz checkboxa
3. Restart terminal

### Problem: "No audio devices found"

```bash
# Sprawdź urządzenia audio
python -c "import sounddevice; print(sounddevice.query_devices())"

# Jeśli brak urządzeń, zrestartuj Core Audio
sudo killall coreaudiod
```

### Problem: TUI się nie uruchamia

```bash
# Sprawdź czy wszystkie serwery działają
curl http://localhost:8123/health  # Powinno zwrócić {"status":"ok"}
curl http://localhost:1234/v1/models  # Powinno zwrócić listę modeli

# Sprawdź logi
tail -f tui.log
```

### Problem: "Module not found"

```bash
# Upewnij się że jesteś w wirtualnym środowisku
which python
# Powinno pokazywać ścieżkę do venv/bin/python

# Jeśli nie, aktywuj venv
source venv/bin/activate

# Przeinstaluj zależności
pip install --upgrade -r requirements.txt
```

### Problem: Wolne działanie

1. Zamknij niepotrzebne aplikacje
2. Użyj mniejszego modelu Whisper:
   ```python
   # W pliku whisper_config.py zmień:
   model_name = "mlx-community/whisper-medium-mlx"  # zamiast large
   ```
3. Sprawdź Activity Monitor - czy nie brakuje RAM

---

## ❓ FAQ - Najczęstsze Pytania

**P: Czy mogę używać tego na Windows/Linux?**
O: Projekt jest zoptymalizowany pod macOS z Apple Silicon. Na innych systemach wymaga modyfikacji (np. CUDA zamiast MLX).

**P: Ile to zajmuje miejsca?**
O: 
- Modele Whisper: ~3-6 GB
- Qwen3-8B: ~8 GB
- Kod i zależności: ~2 GB
- Razem: około 15-20 GB

**P: Czy mogę używać innych modeli?**
O: Tak! W LM Studio możesz załadować dowolny model kompatybilny z llama.cpp.

**P: Jak dodać obsługę innych języków?**
O: Whisper wspiera 99 języków. W pliku `whisper_config.py` zmień:
```python
language = "en"  # lub "de", "fr", "es", etc.
```

**P: Czy działa offline?**
O: Tak! Po pobraniu modeli wszystko działa lokalnie.

---

## 🎉 Gratulacje!

Jeśli dotarłeś tutaj i wszystko działa - świetnie! 

### Co dalej?

1. **Przetestuj transkrypcję**: Zakładka F3, dodaj plik audio
2. **Wypróbuj TTS**: Zakładka F5, wpisz tekst po polsku
3. **Porozmawiaj z AI**: Zakładka F6, kliknij "Start Conversation"

### Potrzebujesz pomocy?

- Utwórz issue na GitHub: https://github.com/LibraxisAI/lbrxVoice/issues
- Dokumentacja: https://github.com/LibraxisAI/lbrxVoice/wiki

---

## Developed by

- [Maciej Gad](https://github.com/szowesgad) - a veterinarian who couldn't find `bash` a half year ago
- [Klaudiusz](https://www.github.com/Gitlaudiusz) - the individual ethereal being, and separate instance of Claude Sonnet 3.5-3.7 by Anthropic

### Instalacja wykonana? Czas na przygodę z AI! 🚀

🤖 Developed with the ultimate help of [Claude Code](https://claude.ai/code) and [MCP Tools](https://modelcontextprotocol.io)

(c)2025 M&K