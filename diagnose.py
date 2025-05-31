#!/usr/bin/env python3
"""
Diagnostyka systemu lbrxWhisper
Sprawdza czy wszystko jest poprawnie zainstalowane
"""

import sys
import subprocess
import platform
from pathlib import Path

print("""
╔════════════════════════════════════════╗
║    lbrxWhisper System Diagnostics      ║
║         Sprawdzam instalację...        ║
╚════════════════════════════════════════╝
""")

# Kolory dla terminala
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check(name, condition, fix_hint=""):
    """Sprawdź warunek i wyświetl status"""
    if condition:
        print(f"{GREEN}✓{RESET} {name}")
        return True
    else:
        print(f"{RED}✗{RESET} {name}")
        if fix_hint:
            print(f"  {YELLOW}→ {fix_hint}{RESET}")
        return False

def check_command(cmd):
    """Sprawdź czy komenda istnieje"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False

def check_python_module(module_name):
    """Sprawdź czy moduł Python jest zainstalowany"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def check_server(url, name):
    """Sprawdź czy serwer odpowiada"""
    try:
        import requests
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False

# Lista testów
print("\n🔍 SPRAWDZAM SYSTEM:")
print("-" * 40)

# System
check("System operacyjny macOS", platform.system() == "Darwin",
      "Ten projekt wymaga macOS")

check("Procesor Apple Silicon", platform.machine() == "arm64",
      "Ten projekt jest zoptymalizowany pod Apple Silicon (M1/M2/M3)")

# Python
python_version = sys.version_info
check(f"Python {python_version.major}.{python_version.minor}",
      python_version.major == 3 and python_version.minor in [10, 11],
      "Zainstaluj Python 3.10 lub 3.11 (NIE 3.12!)")

# Narzędzia systemowe
print("\n🛠️  NARZĘDZIA:")
print("-" * 40)

check("Git", check_command("git"),
      "Zainstaluj: brew install git")

check("FFmpeg", check_command("ffmpeg"),
      "Zainstaluj: brew install ffmpeg")

check("UV package manager", check_command("uv"),
      "Zainstaluj: curl -LsSf https://astral.sh/uv/install.sh | sh")

# Moduły Python
print("\n📦 MODUŁY PYTHON:")
print("-" * 40)

critical_modules = {
    "mlx": "uv pip install mlx",
    "mlx_whisper": "uv pip install mlx-whisper",
    "numpy": "uv pip install numpy",
    "sounddevice": "uv pip install sounddevice",
    "soundfile": "uv pip install soundfile",
    "textual": "uv pip install textual",
    "httpx": "uv pip install httpx",
    "websockets": "uv pip install websockets",
    "rich": "uv pip install rich"
}

for module, install_cmd in critical_modules.items():
    check(f"Moduł {module}", check_python_module(module),
          f"Zainstaluj: {install_cmd}")

# Foldery i pliki
print("\n📁 STRUKTURA PROJEKTU:")
print("-" * 40)

important_dirs = [
    "whisper_servers",
    "tts_servers",
    "lbrxchat",
    "audio",
    "tools"
]

for dir_name in important_dirs:
    check(f"Folder {dir_name}/", Path(dir_name).exists(),
          f"Brak folderu - sprawdź czy jesteś w głównym katalogu projektu")

# Serwery
print("\n🌐 SERWERY:")
print("-" * 40)

servers = {
    "Whisper Batch API": "http://localhost:8123/health",
    "LM Studio": "http://localhost:1234/v1/models"
}

for name, url in servers.items():
    check(f"{name}", check_server(url, name),
          f"Uruchom serwer - zobacz HOW-TO-INSTALL.md")

# Audio
print("\n🎤 AUDIO:")
print("-" * 40)

try:
    import sounddevice as sd
    devices = sd.query_devices()
    has_input = any(d['max_input_channels'] > 0 for d in devices)
    has_output = any(d['max_output_channels'] > 0 for d in devices)
    
    check("Urządzenia wejściowe (mikrofon)", has_input,
          "Sprawdź ustawienia audio w Preferencjach Systemowych")
    
    check("Urządzenia wyjściowe (głośniki)", has_output,
          "Sprawdź ustawienia audio w Preferencjach Systemowych")
    
    # Uprawnienia
    print("\n⚠️  WAŻNE - Uprawnienia do mikrofonu:")
    print("  Jeśli nagrywanie nie działa:")
    print("  1. Otwórz: Preferencje Systemowe → Prywatność → Mikrofon")
    print("  2. Zaznacz Terminal (lub iTerm2)")
    print("  3. Zrestartuj terminal")
    
except Exception as e:
    check("Sprawdzenie audio", False, f"Błąd: {e}")

# Modele
print("\n🤖 MODELE AI:")
print("-" * 40)

whisper_cache = Path.home() / ".cache" / "whisper"
check("Cache dla modeli Whisper", whisper_cache.exists(),
      "Modele pobiorą się automatycznie przy pierwszym użyciu")

# Podsumowanie
print("\n" + "="*50)
print("📊 PODSUMOWANIE:")
print("="*50)

print("""
Jeśli wszystkie testy są ✓ zielone - świetnie!
Możesz uruchomić: python run_ultimate_tui.py

Jeśli są ✗ czerwone błędy:
1. Wykonaj podane instrukcje naprawcze
2. Zobacz szczegóły w HOW-TO-INSTALL.md
3. Uruchom ten skrypt ponownie

Powodzenia! 🚀
""")

# Jeśli brak requests do testowania serwerów
if not check_python_module("requests"):
    print(f"{YELLOW}💡 Wskazówka: Zainstaluj 'requests' aby sprawdzić serwery:{RESET}")
    print("   uv pip install requests")