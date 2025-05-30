#!/usr/bin/env python3
"""
Prosty interaktywny konfigurator Whisper w terminalu
===================================================

Praktyczna wersja TUI do szybkiej konfiguracji parametrów MLX Whisper.

Autor: Maciej Gad & Claude
Data: 2025-05-30
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from whisper_config import WhisperConfig


class SimpleWhisperConfigTUI:
    """Prosty konfigurator Whisper w trybie tekstowym"""
    
    def __init__(self):
        self.config = WhisperConfig()
        self.modified = False
        self.config_groups = {
            "1": {
                "name": "🎯 Podstawowe",
                "params": ["model_name", "language", "task"]
            },
            "2": {
                "name": "🔄 Jakość i powtórzenia",
                "params": ["condition_on_previous_text", "compression_ratio_threshold", 
                          "logprob_threshold", "no_speech_threshold"]
            },
            "3": {
                "name": "🔍 Dekodowanie",
                "params": ["temperature", "beam_size", "best_of", "patience", "length_penalty"]
            },
            "4": {
                "name": "⏱️  Timestampy",
                "params": ["word_timestamps", "prepend_punctuations", "append_punctuations"]
            },
            "5": {
                "name": "💬 Prompt",
                "params": ["initial_prompt"]
            },
            "6": {
                "name": "⚙️  Techniczne",
                "params": ["fp16", "verbose"]
            }
        }
        
        # Opisy parametrów
        self.param_descriptions = {
            "model_name": "Model MLX Whisper (tiny/base/small/medium/large-v3)",
            "language": "Język audio (None=auto, 'pl'=polski)",
            "task": "Zadanie (transcribe/translate)",
            "condition_on_previous_text": "Warunkuj na poprzednim? (False zapobiega powtórzeniom!)",
            "compression_ratio_threshold": "Próg kompresji (1.5-3.0, wykrywa powtórzenia)",
            "logprob_threshold": "Próg prawdopodobieństwa (-2.0 do 0.0)",
            "no_speech_threshold": "Próg braku mowy (0.0-1.0)",
            "temperature": "Temperatura (0.0=deterministyczne)",
            "beam_size": "Wielkość beam search (1-10)",
            "best_of": "Liczba prób (1-10)",
            "patience": "Cierpliwość beam search (0.0-2.0)",
            "length_penalty": "Kara za długość (0.5-2.0)",
            "word_timestamps": "Generuj timestampy słów?",
            "initial_prompt": "Prompt kontekstowy",
            "fp16": "Użyj float16 (szybsze)?",
            "verbose": "Szczegółowe logi?"
        }
    
    def clear_screen(self):
        """Wyczyść ekran"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self):
        """Wyświetl nagłówek"""
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║           🎙️  Konfigurator MLX Whisper - lbrxWhisper          ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
    
    def print_menu(self):
        """Wyświetl menu główne"""
        print("📋 GRUPY PARAMETRÓW:")
        print("─" * 40)
        
        for key, group in self.config_groups.items():
            print(f"  [{key}] {group['name']}")
        
        print("\n🎨 PRESETY:")
        print("─" * 40)
        print("  [P1] Polski zoptymalizowany")
        print("  [P2] Polski wysokiej jakości")
        print("  [P3] Polski szybki")
        print("  [P4] Dla hałaśliwego audio")
        
        print("\n💾 OPERACJE:")
        print("─" * 40)
        print("  [S] Zapisz konfigurację")
        print("  [L] Wczytaj konfigurację")
        print("  [E] Eksportuj kod Python")
        print("  [T] Testuj na pliku audio")
        print("  [R] Reset do domyślnych")
        print("  [Q] Wyjście")
        
        if self.modified:
            print("\n⚠️  Konfiguracja została zmodyfikowana")
    
    def show_group_params(self, group_key: str):
        """Wyświetl parametry grupy"""
        self.clear_screen()
        group = self.config_groups[group_key]
        
        print(f"\n{group['name']}")
        print("=" * 60)
        
        for i, param_name in enumerate(group['params'], 1):
            value = getattr(self.config, param_name)
            desc = self.param_descriptions.get(param_name, "")
            
            # Formatowanie wartości
            if value is None:
                value_str = "None (auto)"
            elif isinstance(value, bool):
                value_str = "✓ Tak" if value else "✗ Nie"
            elif isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            
            print(f"\n[{i}] {param_name}")
            print(f"    📝 {desc}")
            print(f"    ➤  Wartość: {value_str}")
        
        print("\n[0] Powrót do menu")
        print("─" * 60)
        
        choice = input("\nWybierz parametr do edycji (1-{}) lub 0: ".format(len(group['params'])))
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(group['params']):
                param_name = group['params'][idx]
                self.edit_parameter(param_name)
        except ValueError:
            print("❌ Nieprawidłowy wybór")
            input("\nNaciśnij Enter...")
    
    def edit_parameter(self, param_name: str):
        """Edytuj pojedynczy parametr"""
        current_value = getattr(self.config, param_name)
        param_type = type(current_value) if current_value is not None else str
        
        print(f"\n📝 Edycja: {param_name}")
        print(f"Obecna wartość: {current_value}")
        print(f"Opis: {self.param_descriptions.get(param_name, '')}")
        
        # Specjalne przypadki
        if param_name == "model_name":
            print("\nDostępne modele:")
            models = [
                "mlx-community/whisper-tiny-mlx",
                "mlx-community/whisper-base-mlx",
                "mlx-community/whisper-small-mlx",
                "mlx-community/whisper-medium-mlx",
                "mlx-community/whisper-large-v3-mlx"
            ]
            for i, model in enumerate(models, 1):
                size = model.split('-')[-2]
                print(f"  [{i}] {size} - {model}")
            
            choice = input("\nWybierz model (1-5): ")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    setattr(self.config, param_name, models[idx])
                    self.modified = True
                    print(f"✅ Zmieniono na: {models[idx]}")
            except:
                print("❌ Nieprawidłowy wybór")
                
        elif param_name == "language":
            print("\nDostępne języki:")
            print("  [0] None (auto-detect)")
            langs = ["pl", "en", "de", "fr", "es", "it", "pt", "ru", "zh", "ja"]
            for i, lang in enumerate(langs, 1):
                print(f"  [{i}] {lang}")
            
            choice = input("\nWybierz język (0-10): ")
            try:
                idx = int(choice)
                if idx == 0:
                    setattr(self.config, param_name, None)
                elif 1 <= idx <= len(langs):
                    setattr(self.config, param_name, langs[idx-1])
                self.modified = True
                print(f"✅ Zmieniono na: {getattr(self.config, param_name)}")
            except:
                print("❌ Nieprawidłowy wybór")
                
        elif param_name == "task":
            print("\n[1] transcribe (transkrypcja)")
            print("[2] translate (tłumaczenie na angielski)")
            choice = input("\nWybierz zadanie (1-2): ")
            if choice == "1":
                setattr(self.config, param_name, "transcribe")
                self.modified = True
            elif choice == "2":
                setattr(self.config, param_name, "translate")
                self.modified = True
                
        elif param_type == bool:
            print("\n[1] Tak (True)")
            print("[2] Nie (False)")
            choice = input("\nWybierz (1-2): ")
            if choice == "1":
                setattr(self.config, param_name, True)
                self.modified = True
            elif choice == "2":
                setattr(self.config, param_name, False)
                self.modified = True
                
        elif param_type in (int, float):
            try:
                if param_type == int:
                    new_value = int(input(f"\nNowa wartość (int): "))
                else:
                    new_value = float(input(f"\nNowa wartość (float): "))
                
                # Walidacja zakresów
                if param_name == "compression_ratio_threshold" and not (1.5 <= new_value <= 3.0):
                    print("⚠️  Wartość poza zakresem 1.5-3.0")
                elif param_name == "logprob_threshold" and not (-2.0 <= new_value <= 0.0):
                    print("⚠️  Wartość poza zakresem -2.0 do 0.0")
                elif param_name == "no_speech_threshold" and not (0.0 <= new_value <= 1.0):
                    print("⚠️  Wartość poza zakresem 0.0-1.0")
                elif param_name in ["beam_size", "best_of"] and not (1 <= new_value <= 10):
                    print("⚠️  Wartość poza zakresem 1-10")
                else:
                    setattr(self.config, param_name, new_value)
                    self.modified = True
                    print(f"✅ Zmieniono na: {new_value}")
            except ValueError:
                print("❌ Nieprawidłowa wartość")
                
        else:  # string
            new_value = input(f"\nNowa wartość (Enter dla pustej): ").strip()
            if new_value == "" and current_value is None:
                setattr(self.config, param_name, None)
            else:
                setattr(self.config, param_name, new_value)
            self.modified = True
            print(f"✅ Zmieniono na: {new_value or 'None'}")
        
        input("\nNaciśnij Enter...")
    
    def load_preset(self, preset_key: str):
        """Wczytaj preset"""
        if preset_key == "P1":
            self.config = WhisperConfig.polish_optimized()
            print("✅ Wczytano preset: Polski zoptymalizowany")
        elif preset_key == "P2":
            self.config = WhisperConfig.polish_high_quality()
            print("✅ Wczytano preset: Polski wysokiej jakości")
        elif preset_key == "P3":
            self.config = WhisperConfig.polish_fast()
            print("✅ Wczytano preset: Polski szybki")
        elif preset_key == "P4":
            self.config = WhisperConfig.noisy_audio()
            print("✅ Wczytano preset: Dla hałaśliwego audio")
        else:
            print("❌ Nieznany preset")
            return
        
        self.modified = True
        input("\nNaciśnij Enter...")
    
    def save_config(self):
        """Zapisz konfigurację"""
        filename = input("\nNazwa pliku (bez rozszerzenia): ").strip()
        if not filename:
            filename = "whisper_config"
        
        filename = f"{filename}.json"
        
        config_dict = asdict(self.config)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ Zapisano do: {filename}")
        except Exception as e:
            print(f"❌ Błąd zapisu: {e}")
        
        input("\nNaciśnij Enter...")
    
    def load_config(self):
        """Wczytaj konfigurację"""
        # Pokaż dostępne pliki
        json_files = list(Path('.').glob('*.json'))
        if json_files:
            print("\nDostępne pliki konfiguracji:")
            for i, f in enumerate(json_files, 1):
                print(f"  [{i}] {f.name}")
            
            choice = input("\nWybierz plik (numer lub nazwa): ").strip()
            
            try:
                # Sprawdź czy to numer
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    filename = str(json_files[idx])
                else:
                    filename = choice
            except ValueError:
                filename = choice
        else:
            filename = input("\nNazwa pliku do wczytania: ").strip()
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Aktualizuj config
            for key, value in config_dict.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            print(f"✅ Wczytano z: {filename}")
            self.modified = True
        except FileNotFoundError:
            print(f"❌ Nie znaleziono pliku: {filename}")
        except Exception as e:
            print(f"❌ Błąd wczytywania: {e}")
        
        input("\nNaciśnij Enter...")
    
    def export_code(self):
        """Eksportuj kod Python"""
        self.clear_screen()
        print("\n🐍 KOD PYTHON Z AKTUALNĄ KONFIGURACJĄ:")
        print("=" * 70)
        
        code = '''#!/usr/bin/env python3
"""
Skrypt transkrypcji z konfiguracją wygenerowaną przez TUI
"""
import mlx_whisper
from pathlib import Path

# Parametry transkrypcji
config_kwargs = {'''
        
        # Dodaj parametry
        kwargs = self.config.to_transcribe_kwargs()
        for key, value in kwargs.items():
            if key == 'decode_options':
                continue  # Obsłużymy osobno
            if isinstance(value, str):
                code += f'\n    "{key}": "{value}",'
            else:
                code += f'\n    "{key}": {value},'
        
        # Decode options
        if 'decode_options' in kwargs:
            code += '\n    "decode_options": {'
            for key, value in kwargs['decode_options'].items():
                if value is not None:
                    if isinstance(value, str):
                        code += f'\n        "{key}": "{value}",'
                    else:
                        code += f'\n        "{key}": {value},'
            code += '\n    }'
        
        code += '''
}

def transcribe_audio(audio_path: str, output_path: str = None):
    """Transkrybuj plik audio z zapisem do pliku"""
    print(f"Transkrybuję: {audio_path}")
    
    # Transkrypcja
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo="''' + self.config.model_name + '''",
        **config_kwargs
    )
    
    # Wyświetl wynik
    print(f"\\nJęzyk: {result.get('language', 'unknown')}")
    print(f"Tekst:\\n{result['text']}")
    
    # Zapisz do pliku jeśli podano
    if output_path:
        Path(output_path).write_text(result['text'], encoding='utf-8')
        print(f"\\nZapisano do: {output_path}")
    
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Użycie: python skrypt.py <plik_audio> [plik_wyjściowy]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    transcribe_audio(audio_file, output_file)
'''
        
        print(code)
        print("=" * 70)
        
        save = input("\nZapisać do pliku? (t/n): ").lower()
        if save == 't':
            filename = input("Nazwa pliku (bez .py): ").strip() or "transcribe_configured"
            filename = f"{filename}.py"
            
            try:
                Path(filename).write_text(code, encoding='utf-8')
                os.chmod(filename, 0o755)  # Wykonywalne
                print(f"✅ Zapisano do: {filename}")
            except Exception as e:
                print(f"❌ Błąd: {e}")
        
        input("\nNaciśnij Enter...")
    
    def test_config(self):
        """Testuj konfigurację na pliku audio"""
        audio_file = input("\nŚcieżka do pliku audio: ").strip()
        
        if not Path(audio_file).exists():
            print(f"❌ Plik nie istnieje: {audio_file}")
            input("\nNaciśnij Enter...")
            return
        
        print(f"\n🎙️  Testuję transkrypcję z aktualną konfiguracją...")
        print(f"Model: {self.config.model_name}")
        print(f"Język: {self.config.language or 'auto-detect'}")
        print(f"Condition on previous: {self.config.condition_on_previous_text}")
        print("\nTo może chwilę potrwać...\n")
        
        try:
            import mlx_whisper
            
            result = mlx_whisper.transcribe(
                audio_file,
                path_or_hf_repo=self.config.model_name,
                **self.config.to_transcribe_kwargs()
            )
            
            print(f"\n✅ WYNIK TRANSKRYPCJI:")
            print("=" * 60)
            print(f"Język: {result.get('language', 'unknown')}")
            print(f"\nTekst:\n{result['text']}")
            print("=" * 60)
            
            save = input("\nZapisać wynik do pliku? (t/n): ").lower()
            if save == 't':
                output_file = audio_file.replace('.m4a', '_transcribed.txt')
                output_file = output_file.replace('.mp3', '_transcribed.txt')
                output_file = output_file.replace('.wav', '_transcribed.txt')
                
                Path(output_file).write_text(result['text'], encoding='utf-8')
                print(f"✅ Zapisano do: {output_file}")
                
        except Exception as e:
            print(f"❌ Błąd transkrypcji: {e}")
        
        input("\nNaciśnij Enter...")
    
    def run(self):
        """Główna pętla aplikacji"""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()
            
            choice = input("\n➤ Wybór: ").strip().upper()
            
            if choice == 'Q':
                if self.modified:
                    confirm = input("\n⚠️  Masz niezapisane zmiany. Na pewno wyjść? (t/n): ").lower()
                    if confirm != 't':
                        continue
                print("\n👋 Do widzenia!")
                break
            
            elif choice in self.config_groups:
                self.show_group_params(choice)
            
            elif choice in ['P1', 'P2', 'P3', 'P4']:
                self.load_preset(choice)
            
            elif choice == 'S':
                self.save_config()
            
            elif choice == 'L':
                self.load_config()
            
            elif choice == 'E':
                self.export_code()
            
            elif choice == 'T':
                self.test_config()
            
            elif choice == 'R':
                self.config = WhisperConfig()
                self.modified = False
                print("✅ Przywrócono domyślne wartości")
                input("\nNaciśnij Enter...")
            
            else:
                print("❌ Nieznana opcja")
                input("\nNaciśnij Enter...")


def main():
    """Uruchom aplikację"""
    tui = SimpleWhisperConfigTUI()
    
    try:
        tui.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Przerwano przez użytkownika")
        sys.exit(0)


if __name__ == "__main__":
    main()