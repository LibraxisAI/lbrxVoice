#!/usr/bin/env python3
"""
lbrxWhisper - Demo głównych funkcjonalności
==========================================

Ten skrypt demonstruje aktualne możliwości projektu lbrxWhisper:
- Transkrypcja MLX Whisper z optymalizacją dla języka polskiego
- Interaktywna konfiguracja parametrów
- Serwery batch i realtime
- Integracja z TTS (placeholder)

Autor: Maciej Gad & Claude
Data: 2025-05-30
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional
import mlx_whisper
from whisper_config import WhisperConfig


def print_header():
    """Wyświetl nagłówek projektu"""
    print("\n" + "="*70)
    print("                      🎙️  lbrxWhisper Demo")
    print("           MLX-native Whisper dla języka polskiego")
    print("="*70 + "\n")


def show_project_status():
    """Pokaż aktualny stan projektu"""
    print("📊 STAN PROJEKTU:")
    print("─" * 50)
    
    # Co działa
    print("\n✅ Co działa:")
    print("  • Transkrypcja MLX Whisper (wszystkie modele)")
    print("  • Optymalizacja dla języka polskiego")
    print("  • Zapobieganie powtórzeniom (condition_on_previous_text=False)")
    print("  • Batch server na porcie 8123")
    print("  • Realtime WebSocket na porcie 8126")
    print("  • Centralna konfiguracja z presetami")
    print("  • Interaktywny konfigurator TUI")
    print("  • Batch processing wielu plików")
    
    # W trakcie
    print("\n🚧 W trakcie rozwoju:")
    print("  • Implementacja DIA TTS (obecnie placeholder)")
    print("  • Instalacja CSM-MLX TTS")
    print("  • Pełny pipeline: ASR → LLM → TTS")
    print("  • Dashboard TUI z ratatui")
    
    # Problemy
    print("\n⚠️  Znane problemy:")
    print("  • Jakość transkrypcji polskiej wymaga dopracowania")
    print("  • DIA generuje ciszę (brak implementacji)")
    print("  • Format 'text' nie zaimplementowany w API")


def demo_basic_transcription():
    """Demonstracja podstawowej transkrypcji"""
    print("\n\n🎯 DEMO: Podstawowa transkrypcja")
    print("─" * 50)
    
    # Sprawdź czy są pliki testowe
    test_files = list(Path("uploads").glob("*.m4a")) + \
                 list(Path("uploads").glob("*.mp3")) + \
                 list(Path("uploads").glob("*.wav"))
    
    if not test_files:
        print("❌ Brak plików audio w katalogu uploads/")
        return
    
    # Weź pierwszy plik
    audio_file = str(test_files[0])
    print(f"Plik testowy: {audio_file}")
    
    # Użyj optymalnej konfiguracji
    config = WhisperConfig.polish_optimized()
    print(f"\nKonfiguracja: Polski zoptymalizowany")
    print(f"  • Model: {config.model_name}")
    print(f"  • Język: {config.language}")
    print(f"  • condition_on_previous_text: {config.condition_on_previous_text}")
    
    print("\n🔄 Transkrybuję (to może chwilę potrwać)...")
    
    try:
        result = mlx_whisper.transcribe(
            audio_file,
            path_or_hf_repo=config.model_name,
            **config.to_transcribe_kwargs()
        )
        
        print(f"\n✅ Wynik:")
        print(f"Język: {result.get('language', 'unknown')}")
        print(f"Tekst: {result['text'][:200]}..." if len(result['text']) > 200 else f"Tekst: {result['text']}")
        
    except Exception as e:
        print(f"❌ Błąd: {e}")


def demo_config_options():
    """Pokaż różne opcje konfiguracji"""
    print("\n\n🔧 DEMO: Opcje konfiguracji")
    print("─" * 50)
    
    configs = [
        ("Polski zoptymalizowany", WhisperConfig.polish_optimized()),
        ("Polski wysokiej jakości", WhisperConfig.polish_high_quality()),
        ("Polski szybki", WhisperConfig.polish_fast()),
        ("Dla hałaśliwego audio", WhisperConfig.noisy_audio()),
    ]
    
    print("Dostępne presety:")
    for name, config in configs:
        print(f"\n{name}:")
        print(f"  • Model: {config.model_name.split('/')[-1]}")
        print(f"  • Beam size: {config.beam_size}")
        print(f"  • Word timestamps: {config.word_timestamps}")
        print(f"  • Compression ratio: {config.compression_ratio_threshold}")


def demo_server_endpoints():
    """Pokaż endpointy serwerów"""
    print("\n\n🌐 DEMO: Endpointy API")
    print("─" * 50)
    
    print("\nBatch Server (REST API):")
    print("  • URL: http://0.0.0.0:8123/v1/audio/transcriptions")
    print("  • Metoda: POST")
    print("  • Przykład curl:")
    print("""
    curl -X POST http://0.0.0.0:8123/v1/audio/transcriptions \\
      -H "Content-Type: multipart/form-data" \\
      -F "file=@audio.m4a" \\
      -F "language=pl" \\
      -F "response_format=json"
    """)
    
    print("\nRealtime Server (WebSocket):")
    print("  • URL: ws://0.0.0.0:8126/v1/audio/transcriptions")
    print("  • Format: base64 encoded audio chunks")
    print("  • Przykład Python:")
    print("""
    import websocket
    import base64
    
    ws = websocket.WebSocket()
    ws.connect("ws://0.0.0.0:8126/v1/audio/transcriptions")
    
    # Wyślij audio
    with open("audio.m4a", "rb") as f:
        audio_data = base64.b64encode(f.read()).decode()
        ws.send(audio_data)
    
    # Odbierz wynik
    result = ws.recv()
    """)


def interactive_menu():
    """Menu interaktywne"""
    while True:
        print("\n\n📋 MENU GŁÓWNE:")
        print("─" * 50)
        print("  [1] Pokaż stan projektu")
        print("  [2] Demo podstawowej transkrypcji")
        print("  [3] Pokaż opcje konfiguracji")
        print("  [4] Pokaż endpointy API")
        print("  [5] Uruchom konfigurator TUI")
        print("  [6] Uruchom serwery (batch + realtime)")
        print("  [7] Batch transkrypcja katalogu")
        print("  [Q] Wyjście")
        
        choice = input("\n➤ Wybór: ").strip().upper()
        
        if choice == 'Q':
            print("\n👋 Do widzenia!")
            break
        elif choice == '1':
            show_project_status()
        elif choice == '2':
            demo_basic_transcription()
        elif choice == '3':
            demo_config_options()
        elif choice == '4':
            demo_server_endpoints()
        elif choice == '5':
            print("\n🚀 Uruchamiam konfigurator TUI...")
            subprocess.run([sys.executable, "whisper_config_tui.py"])
        elif choice == '6':
            print("\n🚀 Uruchamiam serwery...")
            print("Użyj Ctrl+C aby zatrzymać")
            subprocess.run([sys.executable, "start_servers.py"])
        elif choice == '7':
            input_dir = input("\nKatalog wejściowy [uploads]: ").strip() or "uploads"
            output_dir = input("Katalog wyjściowy [outputs/txt]: ").strip() or "outputs/txt"
            
            print(f"\n🔄 Transkrybuję pliki z {input_dir} do {output_dir}...")
            subprocess.run([
                sys.executable, 
                "batch_transcribe_all.py",
                "--input-dir", input_dir,
                "--output-dir", output_dir,
                "--language", "pl"
            ])
        else:
            print("❌ Nieznana opcja")


def main():
    """Główna funkcja demo"""
    print_header()
    
    # Pokaż podsumowanie
    print("🎯 CEL PROJEKTU:")
    print("Natywna implementacja MLX dla pełnego pipeline'u głosowego:")
    print("Audio → Whisper ASR → LLM → TTS → Audio")
    print("\nAktualnie jesteśmy na etapie integracji i optymalizacji.")
    
    # Sprawdź środowisko
    try:
        import mlx
        print("\n✅ MLX zainstalowane")
    except:
        print("\n❌ Brak MLX - zainstaluj przez: pip install mlx")
        return
    
    # Menu interaktywne
    interactive_menu()


if __name__ == "__main__":
    main()