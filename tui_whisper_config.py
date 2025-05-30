#!/usr/bin/env python3
"""
Interaktywny komponent TUI do zarządzania konfiguracją Whisper
=============================================================

Ten moduł zawiera interaktywny interfejs tekstowy (TUI) do konfiguracji
wszystkich parametrów MLX Whisper. Wspiera mysz, skróty klawiszowe i presety.

Autor: Maciej Gad & Claude
Data: 2025-05-30
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt, Confirm, FloatPrompt, IntPrompt
from rich.columns import Columns
from rich.align import Align
from rich.button import Button
from rich.syntax import Syntax

from whisper_config import WhisperConfig


class ConfigParameter:
    """Reprezentacja pojedynczego parametru konfiguracji"""
    def __init__(
        self, 
        name: str, 
        value: any, 
        param_type: type,
        description: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        choices: Optional[List] = None,
        group: str = "Inne"
    ):
        self.name = name
        self.value = value
        self.param_type = param_type
        self.description = description
        self.min_val = min_val
        self.max_val = max_val
        self.choices = choices
        self.group = group
        self.original_value = value
    
    def reset(self):
        """Przywróć oryginalną wartość"""
        self.value = self.original_value
    
    def format_value(self) -> str:
        """Formatuj wartość do wyświetlenia"""
        if self.value is None:
            return "[dim]None[/dim]"
        elif isinstance(self.value, bool):
            return "[green]✓[/green]" if self.value else "[red]✗[/red]"
        elif isinstance(self.value, (list, tuple)):
            return str(self.value)
        elif isinstance(self.value, float):
            return f"{self.value:.2f}"
        else:
            return str(self.value)


class WhisperConfigTUI:
    """Interaktywny interfejs TUI do konfiguracji Whisper"""
    
    def __init__(self):
        self.console = Console()
        self.config = WhisperConfig()
        self.parameters = self._init_parameters()
        self.current_group = 0
        self.current_param = 0
        self.groups = self._get_groups()
        self.modified = False
        self.message = ""
        
    def _get_groups(self) -> List[str]:
        """Pobierz unikalne grupy parametrów"""
        groups = []
        for param in self.parameters:
            if param.group not in groups:
                groups.append(param.group)
        return groups
    
    def _init_parameters(self) -> List[ConfigParameter]:
        """Zainicjalizuj listę parametrów z opisami"""
        params = [
            # Podstawowe
            ConfigParameter(
                "model_name", self.config.model_name, str,
                "Model MLX Whisper do użycia (tiny/base/small/medium/large-v3)",
                choices=[
                    "mlx-community/whisper-tiny-mlx",
                    "mlx-community/whisper-base-mlx", 
                    "mlx-community/whisper-small-mlx",
                    "mlx-community/whisper-medium-mlx",
                    "mlx-community/whisper-large-v3-mlx"
                ],
                group="Podstawowe"
            ),
            ConfigParameter(
                "language", self.config.language, str,
                "Język audio (None=auto, 'pl'=polski, 'en'=angielski)",
                choices=[None, "pl", "en", "de", "fr", "es", "it", "pt", "ru", "zh", "ja"],
                group="Podstawowe"
            ),
            ConfigParameter(
                "task", self.config.task, str,
                "Zadanie do wykonania",
                choices=["transcribe", "translate"],
                group="Podstawowe"
            ),
            
            # Jakość i powtórzenia
            ConfigParameter(
                "condition_on_previous_text", self.config.condition_on_previous_text, bool,
                "Czy warunkować na poprzednim tekście? (False zapobiega powtórzeniom!)",
                group="Jakość i powtórzenia"
            ),
            ConfigParameter(
                "compression_ratio_threshold", self.config.compression_ratio_threshold, float,
                "Próg współczynnika kompresji (wykrywa powtórzenia)",
                min_val=1.5, max_val=3.0,
                group="Jakość i powtórzenia"
            ),
            ConfigParameter(
                "logprob_threshold", self.config.logprob_threshold, float,
                "Próg logarytmu prawdopodobieństwa",
                min_val=-2.0, max_val=0.0,
                group="Jakość i powtórzenia"
            ),
            ConfigParameter(
                "no_speech_threshold", self.config.no_speech_threshold, float,
                "Próg prawdopodobieństwa braku mowy",
                min_val=0.0, max_val=1.0,
                group="Jakość i powtórzenia"
            ),
            
            # Dekodowanie
            ConfigParameter(
                "temperature", self.config.temperature, float,
                "Temperatura (0.0=deterministyczne, >0=losowe)",
                min_val=0.0, max_val=2.0,
                group="Dekodowanie"
            ),
            ConfigParameter(
                "beam_size", self.config.beam_size, int,
                "Wielkość beam search (gdy temperature=0.0)",
                min_val=1, max_val=10,
                group="Dekodowanie"
            ),
            ConfigParameter(
                "best_of", self.config.best_of, int,
                "Liczba niezależnych prób (gdy temperature>0.0)",
                min_val=1, max_val=10,
                group="Dekodowanie"
            ),
            ConfigParameter(
                "patience", self.config.patience, float,
                "Cierpliwość w beam search",
                min_val=0.0, max_val=2.0,
                group="Dekodowanie"
            ),
            ConfigParameter(
                "length_penalty", self.config.length_penalty, float,
                "Kara za długość (<1=krótsze, >1=dłuższe)",
                min_val=0.5, max_val=2.0,
                group="Dekodowanie"
            ),
            
            # Timestampy
            ConfigParameter(
                "word_timestamps", self.config.word_timestamps, bool,
                "Czy generować timestampy dla słów?",
                group="Timestampy"
            ),
            ConfigParameter(
                "prepend_punctuations", self.config.prepend_punctuations, str,
                "Znaki do łączenia z następnym słowem",
                group="Timestampy"
            ),
            ConfigParameter(
                "append_punctuations", self.config.append_punctuations, str,
                "Znaki do łączenia z poprzednim słowem",
                group="Timestampy"
            ),
            
            # Prompt
            ConfigParameter(
                "initial_prompt", self.config.initial_prompt, str,
                "Początkowy prompt kontekstowy",
                group="Prompt i kontekst"
            ),
            
            # Techniczne
            ConfigParameter(
                "fp16", self.config.fp16, bool,
                "Czy używać float16 (szybsze) czy float32 (dokładniejsze)?",
                group="Techniczne"
            ),
            ConfigParameter(
                "verbose", self.config.verbose, bool,
                "Poziom szczegółowości logów",
                group="Techniczne"
            ),
        ]
        
        return params
    
    def get_params_for_group(self, group: str) -> List[ConfigParameter]:
        """Pobierz parametry dla danej grupy"""
        return [p for p in self.parameters if p.group == group]
    
    def create_main_layout(self) -> Layout:
        """Utwórz główny layout aplikacji"""
        layout = Layout()
        
        # Podział na sekcje
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=4)
        )
        
        # Podział body na kolumny
        layout["body"].split_row(
            Layout(name="groups", ratio=1),
            Layout(name="params", ratio=2),
            Layout(name="preview", ratio=2)
        )
        
        return layout
    
    def render_header(self) -> Panel:
        """Renderuj nagłówek"""
        header_text = Text()
        header_text.append("⚙️  Konfiguracja MLX Whisper", style="bold cyan")
        header_text.append(" - Interaktywny edytor parametrów", style="dim")
        
        return Panel(
            Align.center(header_text),
            border_style="cyan",
            box=None
        )
    
    def render_groups(self) -> Panel:
        """Renderuj listę grup"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        
        for i, group in enumerate(self.groups):
            params_count = len(self.get_params_for_group(group))
            style = "bold cyan" if i == self.current_group else "dim"
            prefix = "▶ " if i == self.current_group else "  "
            
            table.add_row(
                f"{prefix}{group}",
                f"[dim]({params_count})[/dim]",
                style=style
            )
        
        return Panel(
            table,
            title="[bold]Grupy parametrów[/bold]",
            title_align="left",
            border_style="blue"
        )
    
    def render_params(self) -> Panel:
        """Renderuj parametry aktualnej grupy"""
        current_group_name = self.groups[self.current_group]
        params = self.get_params_for_group(current_group_name)
        
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Parametr", style="yellow")
        table.add_column("Wartość", style="green")
        table.add_column("Opis", style="dim")
        
        for i, param in enumerate(params):
            is_selected = i == self.current_param
            
            # Formatowanie wartości
            value_str = param.format_value()
            if param.value != param.original_value:
                value_str = f"[bold]{value_str}[/bold] [dim yellow]●[/dim]"
            
            # Styl wiersza
            row_style = "bold" if is_selected else None
            prefix = "→ " if is_selected else "  "
            
            table.add_row(
                f"{prefix}{param.name}",
                value_str,
                param.description[:40] + "..." if len(param.description) > 40 else param.description,
                style=row_style
            )
        
        return Panel(
            table,
            title=f"[bold]{current_group_name}[/bold]",
            title_align="left",
            border_style="green"
        )
    
    def render_preview(self) -> Panel:
        """Renderuj podgląd aktualnego parametru"""
        current_group_name = self.groups[self.current_group]
        params = self.get_params_for_group(current_group_name)
        
        if not params or self.current_param >= len(params):
            return Panel("Brak parametru do wyświetlenia", border_style="red")
        
        param = params[self.current_param]
        
        # Szczegółowe info o parametrze
        info = Table(show_header=False, box=None, padding=(0, 1))
        info.add_row("[bold]Nazwa:[/bold]", param.name)
        info.add_row("[bold]Typ:[/bold]", param.param_type.__name__)
        info.add_row("[bold]Wartość:[/bold]", param.format_value())
        info.add_row("[bold]Oryginalna:[/bold]", str(param.original_value))
        
        if param.min_val is not None:
            info.add_row("[bold]Min:[/bold]", str(param.min_val))
        if param.max_val is not None:
            info.add_row("[bold]Max:[/bold]", str(param.max_val))
        if param.choices:
            choices_str = "\n".join([f"  • {c}" for c in param.choices[:5]])
            if len(param.choices) > 5:
                choices_str += f"\n  ... i {len(param.choices)-5} więcej"
            info.add_row("[bold]Opcje:[/bold]", choices_str)
        
        # Pełny opis
        desc_panel = Panel(
            param.description,
            title="Opis",
            border_style="dim",
            padding=(1, 2)
        )
        
        # Przykład użycia
        example = self._get_param_example(param.name)
        if example:
            example_panel = Panel(
                Syntax(example, "python", theme="monokai", line_numbers=False),
                title="Przykład",
                border_style="dim"
            )
        else:
            example_panel = ""
        
        # Złóż wszystko
        content = Columns([info])
        if example:
            content = f"{content}\n\n{desc_panel}\n\n{example_panel}"
        else:
            content = f"{content}\n\n{desc_panel}"
        
        return Panel(
            content,
            title=f"[bold]Szczegóły: {param.name}[/bold]",
            title_align="left",
            border_style="yellow"
        )
    
    def _get_param_example(self, param_name: str) -> Optional[str]:
        """Zwróć przykład użycia dla parametru"""
        examples = {
            "condition_on_previous_text": """# Zapobieganie powtórzeniom
result = mlx_whisper.transcribe(
    audio,
    condition_on_previous_text=False  # Kluczowe!
)""",
            "initial_prompt": """# Prompt kontekstowy
result = mlx_whisper.transcribe(
    audio,
    initial_prompt="Rozmowa o AI w weterynarii."
)""",
            "temperature": """# Deterministyczne vs losowe
# Deterministyczne (zawsze ten sam wynik)
temperature=0.0

# Losowe z fallback
temperature=(0.0, 0.2, 0.4)""",
            "compression_ratio_threshold": """# Detekcja powtórzeń
# Wyższa wartość = bardziej restrykcyjna
compression_ratio_threshold=2.8  # dla problemów""",
        }
        return examples.get(param_name)
    
    def render_footer(self) -> Panel:
        """Renderuj stopkę z instrukcjami"""
        shortcuts = Table(show_header=False, box=None)
        shortcuts.add_column("Skrót", style="bold cyan")
        shortcuts.add_column("Akcja", style="dim")
        
        shortcuts.add_row("↑/↓", "Nawiguj parametry")
        shortcuts.add_row("←/→", "Zmień grupę")
        shortcuts.add_row("Enter", "Edytuj wartość")
        shortcuts.add_row("Space", "Toggle bool")
        shortcuts.add_row("r", "Reset parametru")
        shortcuts.add_row("R", "Reset wszystkich")
        shortcuts.add_row("p", "Wczytaj preset")
        shortcuts.add_row("s", "Zapisz config")
        shortcuts.add_row("l", "Wczytaj config")
        shortcuts.add_row("q/Esc", "Wyjście")
        
        # Dodaj komunikat jeśli jest
        if self.message:
            message_text = f"\n[bold yellow]{self.message}[/bold]"
        else:
            message_text = ""
        
        return Panel(
            f"{shortcuts}{message_text}",
            title="[bold]Skróty klawiszowe[/bold]",
            title_align="left",
            border_style="dim"
        )
    
    def edit_parameter(self, param: ConfigParameter):
        """Edytuj wartość parametru"""
        self.console.clear()
        
        # Nagłówek
        self.console.print(f"\n[bold cyan]Edycja parametru: {param.name}[/bold cyan]\n")
        self.console.print(f"Opis: {param.description}")
        self.console.print(f"Typ: {param.param_type.__name__}")
        self.console.print(f"Obecna wartość: {param.value}\n")
        
        try:
            if param.param_type == bool:
                # Toggle dla bool
                param.value = not param.value
                self.modified = True
                self.message = f"Zmieniono {param.name} na {param.value}"
                
            elif param.choices:
                # Wybór z listy
                self.console.print("[bold]Dostępne opcje:[/bold]")
                for i, choice in enumerate(param.choices):
                    current = " [green]← obecna[/green]" if choice == param.value else ""
                    self.console.print(f"  {i}: {choice}{current}")
                
                choice_idx = IntPrompt.ask(
                    "\nWybierz numer opcji",
                    default=param.choices.index(param.value) if param.value in param.choices else 0
                )
                
                if 0 <= choice_idx < len(param.choices):
                    param.value = param.choices[choice_idx]
                    self.modified = True
                    self.message = f"Zmieniono {param.name} na {param.value}"
                
            elif param.param_type == int:
                # Input dla int
                if param.min_val is not None:
                    self.console.print(f"Min: {param.min_val}")
                if param.max_val is not None:
                    self.console.print(f"Max: {param.max_val}")
                
                new_val = IntPrompt.ask(
                    "\nNowa wartość",
                    default=param.value or 0
                )
                
                # Walidacja zakresu
                if param.min_val is not None and new_val < param.min_val:
                    new_val = param.min_val
                if param.max_val is not None and new_val > param.max_val:
                    new_val = param.max_val
                
                param.value = new_val
                self.modified = True
                self.message = f"Zmieniono {param.name} na {param.value}"
                
            elif param.param_type == float:
                # Input dla float
                if param.min_val is not None:
                    self.console.print(f"Min: {param.min_val}")
                if param.max_val is not None:
                    self.console.print(f"Max: {param.max_val}")
                
                new_val = FloatPrompt.ask(
                    "\nNowa wartość",
                    default=param.value or 0.0
                )
                
                # Walidacja zakresu
                if param.min_val is not None and new_val < param.min_val:
                    new_val = param.min_val
                if param.max_val is not None and new_val > param.max_val:
                    new_val = param.max_val
                
                param.value = new_val
                self.modified = True
                self.message = f"Zmieniono {param.name} na {param.value}"
                
            elif param.param_type == str:
                # Input dla string
                new_val = Prompt.ask(
                    "\nNowa wartość",
                    default=param.value or ""
                )
                
                # None jeśli pusty string i była wartość None
                if new_val == "" and param.original_value is None:
                    param.value = None
                else:
                    param.value = new_val
                    
                self.modified = True
                self.message = f"Zmieniono {param.name} na {param.value}"
                
        except KeyboardInterrupt:
            self.message = "Anulowano edycję"
    
    def load_preset(self):
        """Wczytaj preset konfiguracji"""
        self.console.clear()
        self.console.print("\n[bold cyan]Dostępne presety:[/bold cyan]\n")
        
        presets = [
            ("1", "polish_optimized", "Optymalny dla języka polskiego"),
            ("2", "polish_high_quality", "Maksymalna jakość (wolniej)"),
            ("3", "polish_fast", "Szybka transkrypcja"),
            ("4", "noisy_audio", "Dla nagrań z szumami"),
        ]
        
        for key, name, desc in presets:
            self.console.print(f"  [{key}] {name} - {desc}")
        
        choice = Prompt.ask("\nWybierz preset (1-4)", default="1")
        
        if choice == "1":
            self.config = WhisperConfig.polish_optimized()
        elif choice == "2":
            self.config = WhisperConfig.polish_high_quality()
        elif choice == "3":
            self.config = WhisperConfig.polish_fast()
        elif choice == "4":
            self.config = WhisperConfig.noisy_audio()
        else:
            self.message = "Nieprawidłowy wybór"
            return
            
        # Odśwież parametry
        self._update_params_from_config()
        self.message = f"Wczytano preset: {presets[int(choice)-1][1]}"
        self.modified = True
    
    def _update_params_from_config(self):
        """Zaktualizuj parametry z obiektu config"""
        for param in self.parameters:
            param.value = getattr(self.config, param.name)
            param.original_value = param.value
    
    def save_config(self):
        """Zapisz konfigurację do pliku"""
        self.console.clear()
        filename = Prompt.ask(
            "\n[bold cyan]Nazwa pliku do zapisu[/bold cyan]",
            default="whisper_config_saved.json"
        )
        
        # Przygotuj dane do zapisu
        config_dict = {}
        for param in self.parameters:
            config_dict[param.name] = param.value
        
        try:
            path = Path(filename)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self.message = f"Zapisano konfigurację do {filename}"
        except Exception as e:
            self.message = f"Błąd zapisu: {e}"
    
    def load_config(self):
        """Wczytaj konfigurację z pliku"""
        self.console.clear()
        filename = Prompt.ask(
            "\n[bold cyan]Nazwa pliku do wczytania[/bold cyan]",
            default="whisper_config_saved.json"
        )
        
        try:
            path = Path(filename)
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Zastosuj wartości
            for param in self.parameters:
                if param.name in config_dict:
                    param.value = config_dict[param.name]
                    param.original_value = param.value
            
            self.message = f"Wczytano konfigurację z {filename}"
            self.modified = True
        except FileNotFoundError:
            self.message = f"Nie znaleziono pliku {filename}"
        except Exception as e:
            self.message = f"Błąd wczytywania: {e}"
    
    def export_code(self):
        """Eksportuj kod Python z aktualną konfiguracją"""
        code = """import mlx_whisper
from whisper_config import WhisperConfig

# Konfiguracja wygenerowana przez TUI
config = WhisperConfig(
"""
        
        # Dodaj tylko zmienione parametry
        changed_params = []
        for param in self.parameters:
            if param.value != WhisperConfig().__dict__.get(param.name):
                if isinstance(param.value, str):
                    value_str = f'"{param.value}"'
                else:
                    value_str = str(param.value)
                changed_params.append(f"    {param.name}={value_str}")
        
        code += ",\n".join(changed_params)
        code += """
)

# Użycie
result = mlx_whisper.transcribe(
    "audio.m4a",
    path_or_hf_repo=config.model_name,
    **config.to_transcribe_kwargs()
)
"""
        
        return code
    
    async def run(self):
        """Główna pętla aplikacji"""
        layout = self.create_main_layout()
        
        with Live(layout, refresh_per_second=10, screen=True) as live:
            while True:
                # Aktualizuj layout
                layout["header"].update(self.render_header())
                layout["groups"].update(self.render_groups())
                layout["params"].update(self.render_params())
                layout["preview"].update(self.render_preview())
                layout["footer"].update(self.render_footer())
                
                # Czytaj input (nieblokujący)
                try:
                    key = self.console.input(no_input=True)
                    
                    if key in ['q', '\x1b']:  # q lub ESC
                        if self.modified:
                            # Pokaż wygenerowany kod przed wyjściem
                            self.console.clear()
                            self.console.print("\n[bold cyan]Wygenerowany kod:[/bold cyan]\n")
                            self.console.print(Syntax(
                                self.export_code(), 
                                "python", 
                                theme="monokai",
                                line_numbers=True
                            ))
                            self.console.print("\n[dim]Naciśnij Enter aby wyjść...[/dim]")
                            input()
                        break
                    
                    # Nawigacja parametrów
                    elif key == '\x1b[A':  # Strzałka w górę
                        current_group_name = self.groups[self.current_group]
                        params = self.get_params_for_group(current_group_name)
                        if params and self.current_param > 0:
                            self.current_param -= 1
                        self.message = ""
                    
                    elif key == '\x1b[B':  # Strzałka w dół
                        current_group_name = self.groups[self.current_group]
                        params = self.get_params_for_group(current_group_name)
                        if params and self.current_param < len(params) - 1:
                            self.current_param += 1
                        self.message = ""
                    
                    # Nawigacja grup
                    elif key == '\x1b[D':  # Strzałka w lewo
                        if self.current_group > 0:
                            self.current_group -= 1
                            self.current_param = 0
                        self.message = ""
                    
                    elif key == '\x1b[C':  # Strzałka w prawo
                        if self.current_group < len(self.groups) - 1:
                            self.current_group += 1
                            self.current_param = 0
                        self.message = ""
                    
                    # Edycja parametru
                    elif key == '\r':  # Enter
                        current_group_name = self.groups[self.current_group]
                        params = self.get_params_for_group(current_group_name)
                        if params and self.current_param < len(params):
                            self.edit_parameter(params[self.current_param])
                    
                    # Toggle bool
                    elif key == ' ':  # Spacja
                        current_group_name = self.groups[self.current_group]
                        params = self.get_params_for_group(current_group_name)
                        if params and self.current_param < len(params):
                            param = params[self.current_param]
                            if param.param_type == bool:
                                param.value = not param.value
                                self.modified = True
                                self.message = f"Zmieniono {param.name} na {param.value}"
                    
                    # Reset
                    elif key == 'r':
                        current_group_name = self.groups[self.current_group]
                        params = self.get_params_for_group(current_group_name)
                        if params and self.current_param < len(params):
                            param = params[self.current_param]
                            param.reset()
                            self.message = f"Zresetowano {param.name}"
                    
                    elif key == 'R':
                        for param in self.parameters:
                            param.reset()
                        self.message = "Zresetowano wszystkie parametry"
                        self.modified = False
                    
                    # Presety i zapis/odczyt
                    elif key == 'p':
                        self.load_preset()
                    
                    elif key == 's':
                        self.save_config()
                    
                    elif key == 'l':
                        self.load_config()
                    
                    elif key == 'e':
                        # Eksportuj kod
                        self.console.clear()
                        self.console.print("\n[bold cyan]Wygenerowany kod:[/bold cyan]\n")
                        self.console.print(Syntax(
                            self.export_code(), 
                            "python", 
                            theme="monokai",
                            line_numbers=True
                        ))
                        self.console.print("\n[dim]Naciśnij Enter aby kontynuować...[/dim]")
                        input()
                        self.message = "Wyświetlono kod"
                    
                except:
                    # Brak inputu lub błąd - kontynuuj
                    pass
                
                # Krótkie opóźnienie
                await asyncio.sleep(0.1)


def main():
    """Uruchom aplikację TUI"""
    app = WhisperConfigTUI()
    
    try:
        # Próbuj asyncio (dla lepszej responsywności)
        asyncio.run(app.run())
    except:
        # Fallback do synchronicznej wersji
        app.console.print("[yellow]Uwaga: Uruchamiam w trybie synchronicznym[/yellow]")
        # Tu można dodać prostszą wersję synchroniczną
        

if __name__ == "__main__":
    main()