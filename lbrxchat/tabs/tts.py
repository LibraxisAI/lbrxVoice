"""
Tab 5: Text-to-Speech Synthesis
Integrates with tts_servers (DIA, CSM) and other TTS models
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, Button, Select, TextArea, RichLog,
    Label, RadioSet, RadioButton, ProgressBar
)
from textual.reactive import reactive

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class TTSTab(Container):
    """TTS synthesis with multiple model support"""
    
    # Model configurations
    TTS_MODELS = {
        "xtts": {
            "name": "coqui/xtts-v2",
            "languages": ["pl", "en", "de", "fr", "es"],
            "endpoint": None,  # Would use local model
            "supports_voice_cloning": True
        },
        "dia": {
            "name": "nari-labs/Dia-1.6B",
            "languages": ["en"],
            "endpoint": "http://localhost:8124",
            "supports_voice_cloning": False
        },
        "csm": {
            "name": "senstella/csm-1b-mlx",
            "languages": ["en"],
            "endpoint": "http://localhost:8125",
            "supports_voice_cloning": False
        },
        "chatterbox": {
            "name": "ResembleAI/chatterbox",
            "languages": ["en"],
            "endpoint": None,
            "supports_voice_cloning": True
        }
    }
    
    # Reactive state
    selected_model = reactive("xtts")
    selected_language = reactive("pl")
    
    def __init__(self):
        super().__init__()
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.current_job_id = None
        
    def compose(self) -> ComposeResult:
        yield Static("[bold]🔊 Text-to-Speech Synthesis[/bold]")
        
        with Horizontal(classes="tts-layout"):
            # Left panel - Model selection and settings
            with Vertical(classes="tts-settings"):
                yield Static("Select TTS Model:")
                yield RadioSet(
                    RadioButton("coqui/xtts-v2 [PL] ✅", id="model-xtts", value=True),
                    RadioButton("nari-labs/Dia-1.6B", id="model-dia"),
                    RadioButton("senstella/csm-1b-mlx", id="model-csm"),
                    RadioButton("ResembleAI/chatterbox", id="model-chatterbox"),
                    id="model-select"
                )
                
                yield Static("\nLanguage:")
                yield Select(
                    options=[
                        ("pl", "🇵🇱 Polish"),
                        ("en", "🇬🇧 English"),
                        ("de", "🇩🇪 German"),
                        ("fr", "🇫🇷 French"),
                        ("es", "🇪🇸 Spanish")
                    ],
                    id="language-select"
                )
                
                yield Static("\nVoice Settings:")
                yield Label("Speed:")
                yield Select(
                    options=[
                        ("0.5", "0.5x (Very Slow)"),
                        ("0.75", "0.75x (Slow)"),
                        ("1.0", "1.0x (Normal)"),
                        ("1.25", "1.25x (Fast)"),
                        ("1.5", "1.5x (Very Fast)"),
                        ("2.0", "2.0x (Double Speed)")
                    ],
                    id="speed-select"
                )
                
                yield Label("Pitch:")
                yield Select(
                    options=[
                        ("-12", "-12 (Very Low)"),
                        ("-6", "-6 (Low)"),
                        ("0", "0 (Normal)"),
                        ("6", "6 (High)"),
                        ("12", "12 (Very High)")
                    ],
                    id="pitch-select"
                )
                
                yield Static("\nVoice Selection:")
                yield Select(
                    options=[
                        ("female-pl-1", "Female Polish 1"),
                        ("male-pl-1", "Male Polish 1"),
                        ("female-en-1", "Female English 1"),
                        ("male-en-1", "Male English 1")
                    ],
                    id="voice-select"
                )
            
            # Right panel - Additional options
            with Vertical(classes="tts-options"):
                yield Static("Additional Options:")
                
                yield Button(
                    "🎤 Voice Cloning",
                    id="voice-clone",
                    disabled=False
                )
                
                yield Button(
                    "📁 Load from File",
                    id="load-text"
                )
                
                yield Button(
                    "💾 Save Settings",
                    id="save-settings"
                )
                
                yield Static("\nOutput Format:")
                yield RadioSet(
                    RadioButton("WAV (Uncompressed)", value=True),
                    RadioButton("MP3 (Compressed)"),
                    RadioButton("FLAC (Lossless)"),
                    id="format-select"
                )
        
        # Text input area
        yield Static("\n[bold]Input Text:[/bold]")
        yield TextArea(
            "Wprowadź tekst do syntezy mowy lub załaduj z pliku...",
            id="tts-input",
            language="polish"
        )
        
        # Action buttons
        with Horizontal(classes="tts-actions"):
            yield Button(
                "🔊 Generate Speech",
                id="generate-tts",
                variant="primary"
            )
            yield Button(
                "▶️ Preview",
                id="preview-tts",
                disabled=True
            )
            yield Button(
                "⏹️ Stop",
                id="stop-tts",
                disabled=True
            )
        
        # Log output
        yield Static("\n[bold]Output Log:[/bold]")
        yield RichLog(id="tts-log", max_lines=10)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "generate-tts":
            await self.generate_speech()
        elif button_id == "preview-tts":
            await self.preview_speech()
        elif button_id == "stop-tts":
            await self.stop_generation()
        elif button_id == "load-text":
            await self.load_text_file()
        elif button_id == "voice-clone":
            await self.open_voice_cloning()
        elif button_id == "save-settings":
            await self.save_tts_settings()
    
    async def generate_speech(self) -> None:
        """Generate speech from text"""
        log = self.query_one("#tts-log", RichLog)
        text_area = self.query_one("#tts-input", TextArea)
        
        text = text_area.text.strip()
        if not text:
            log.write("[red]Please enter some text![/red]")
            return
        
        # Get selected model
        model_id = self.selected_model
        model_config = self.TTS_MODELS[model_id]
        
        # Check language support
        if self.selected_language not in model_config["languages"]:
            log.write(f"[red]{model_config['name']} doesn't support {self.selected_language}![/red]")
            return
        
        # Update UI
        self.query_one("#generate-tts").disabled = True
        self.query_one("#stop-tts").disabled = False
        
        log.write(f"[cyan]Generating speech with {model_config['name']}...[/cyan]")
        
        try:
            if model_config["endpoint"]:
                # Use REST API (DIA or CSM)
                await self.generate_via_api(text, model_config)
            else:
                # Use local model (xtts or chatterbox)
                await self.generate_local(text, model_config)
                
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
        finally:
            self.query_one("#generate-tts").disabled = False
            self.query_one("#stop-tts").disabled = True
    
    async def generate_via_api(self, text: str, model_config: Dict) -> None:
        """Generate speech using REST API"""
        log = self.query_one("#tts-log", RichLog)
        
        # Prepare request
        endpoint = model_config["endpoint"]
        
        # Check which server (DIA or CSM)
        if "dia" in model_config["name"].lower():
            # DIA API format
            response = await self.http_client.post(
                f"{endpoint}/synthesize",
                json={
                    "text": text,
                    "voice_id": self.query_one("#voice-select").value,
                    "speed": float(self.query_one("#speed-select").value),
                    "pitch": int(self.query_one("#pitch-select").value)
                }
            )
        else:
            # CSM API format
            response = await self.http_client.post(
                f"{endpoint}/synthesize",
                json={
                    "text": text,
                    "speaker_id": 0,  # CSM uses numeric IDs
                    "speed": float(self.query_one("#speed-select").value)
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            self.current_job_id = job_id
            
            log.write(f"[yellow]Job created: {job_id}[/yellow]")
            
            # Poll for completion
            await self.poll_job_status(endpoint, job_id)
        else:
            log.write(f"[red]API error: {response.status_code}[/red]")
    
    async def poll_job_status(self, endpoint: str, job_id: str) -> None:
        """Poll job status until completion"""
        log = self.query_one("#tts-log", RichLog)
        
        while True:
            response = await self.http_client.get(f"{endpoint}/status/{job_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                if status["status"] == "completed":
                    audio_url = status.get("audio_url", "")
                    log.write(f"[green]✓ Speech generated successfully![/green]")
                    
                    # Download and save audio
                    await self.save_audio(endpoint + audio_url, job_id)
                    
                    # Enable preview
                    self.query_one("#preview-tts").disabled = False
                    break
                    
                elif status["status"] == "failed":
                    log.write(f"[red]Generation failed: {status.get('error')}[/red]")
                    break
                    
                else:
                    # Still processing
                    await asyncio.sleep(1)
            else:
                log.write(f"[red]Failed to check status[/red]")
                break
    
    async def generate_local(self, text: str, model_config: Dict) -> None:
        """Generate speech using local model"""
        log = self.query_one("#tts-log", RichLog)
        
        # Import our XTTS implementation
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from tts_servers.xtts_mlx import SimpleXTTSMLX
        from audio.recorder import AudioPlayer
        
        log.write(f"[yellow]Generating with {model_config['name']}...[/yellow]")
        
        try:
            # Initialize XTTS
            tts = SimpleXTTSMLX()
            
            # Get settings
            voice = self.query_one("#voice-select").value or "female-pl-1"
            speed = float(self.query_one("#speed-select").value or "1.0")
            pitch = float(self.query_one("#pitch-select").value or "0")
            
            # Generate audio
            audio_data = tts.synthesize(
                text=text,
                language=self.selected_language,
                voice=voice,
                speed=speed,
                pitch=1.0 + pitch/12  # Convert semitones to ratio
            )
            
            # Save output
            output_dir = Path("outputs/tts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"speech_{timestamp}.wav"
            
            import soundfile as sf
            sf.write(str(output_file), audio_data, tts.sample_rate)
            
            log.write(f"[green]✓ Generated: {output_file.name}[/green]")
            log.write(f"[dim]Duration: {len(audio_data)/tts.sample_rate:.1f}s[/dim]")
            
            # Store for preview
            self.last_audio_file = str(output_file)
            self.last_audio_data = audio_data
            self.last_sample_rate = tts.sample_rate
            
            self.query_one("#preview-tts").disabled = False
            
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
    
    async def save_audio(self, audio_url: str, job_id: str) -> None:
        """Download and save generated audio"""
        log = self.query_one("#tts-log", RichLog)
        
        response = await self.http_client.get(audio_url)
        if response.status_code == 200:
            # Save audio file
            output_dir = Path("outputs/tts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"speech_{self.selected_model}_{timestamp}.wav"
            
            output_file.write_bytes(response.content)
            log.write(f"[green]Saved to: {output_file}[/green]")
    
    async def preview_speech(self) -> None:
        """Preview generated speech"""
        log = self.query_one("#tts-log", RichLog)
        
        if not hasattr(self, 'last_audio_data'):
            log.write("[red]No audio to preview![/red]")
            return
        
        try:
            # Import audio player
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from audio.recorder import AudioPlayer
            
            # Create player
            player = AudioPlayer(sample_rate=self.last_sample_rate)
            
            log.write("[cyan]▶️ Playing audio...[/cyan]")
            
            # Play audio
            player.play(self.last_audio_data, blocking=False)
            
            # Update button states
            self.query_one("#preview-tts").disabled = True
            self.query_one("#stop-tts").disabled = False
            
            # Wait for playback to finish
            duration = len(self.last_audio_data) / self.last_sample_rate
            await asyncio.sleep(duration)
            
            # Reset buttons
            self.query_one("#preview-tts").disabled = False
            self.query_one("#stop-tts").disabled = True
            
            log.write("[green]✓ Playback finished[/green]")
            
        except Exception as e:
            log.write(f"[red]Playback error: {e}[/red]")
    
    async def stop_generation(self) -> None:
        """Stop ongoing generation"""
        log = self.query_one("#tts-log", RichLog)
        
        if self.current_job_id:
            # Cancel job via API
            log.write(f"[yellow]Cancelling job {self.current_job_id}...[/yellow]")
            # API call would go here
        
        self.query_one("#generate-tts").disabled = False
        self.query_one("#stop-tts").disabled = True
    
    async def load_text_file(self) -> None:
        """Load text from file"""
        log = self.query_one("#tts-log", RichLog)
        text_area = self.query_one("#tts-input", TextArea)
        
        # In real implementation, this would open a file dialog
        # For demo, load a sample file
        sample_file = Path("examples/sample_text.txt")
        if sample_file.exists():
            text = sample_file.read_text(encoding='utf-8')
            text_area.text = text
            log.write(f"[green]Loaded: {sample_file}[/green]")
        else:
            log.write("[yellow]No sample file found[/yellow]")
    
    async def open_voice_cloning(self) -> None:
        """Open voice cloning interface"""
        log = self.query_one("#tts-log", RichLog)
        
        if self.TTS_MODELS[self.selected_model]["supports_voice_cloning"]:
            log.write("[cyan]Voice cloning interface (not implemented)[/cyan]")
            # This would open a modal to:
            # 1. Upload reference audio
            # 2. Set voice parameters
            # 3. Test cloned voice
        else:
            log.write("[red]Selected model doesn't support voice cloning[/red]")
    
    async def save_tts_settings(self) -> None:
        """Save current TTS settings"""
        log = self.query_one("#tts-log", RichLog)
        
        settings = {
            "model": self.selected_model,
            "language": self.selected_language,
            "speed": float(self.query_one("#speed-select").value),
            "pitch": int(self.query_one("#pitch-select").value),
            "voice": self.query_one("#voice-select").value
        }
        
        # Save to config file
        config_file = Path("config/tts_settings.json")
        config_file.parent.mkdir(exist_ok=True)
        
        import json
        config_file.write_text(json.dumps(settings, indent=2))
        
        log.write("[green]Settings saved![/green]")
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle model selection change"""
        if event.radio_set.id == "model-select":
            # Map button ID to model key
            model_map = {
                "model-xtts": "xtts",
                "model-dia": "dia",
                "model-csm": "csm",
                "model-chatterbox": "chatterbox"
            }
            
            for button_id, model_key in model_map.items():
                if event.pressed.id == button_id:
                    self.selected_model = model_key
                    self.update_language_options()
                    break
    
    def update_language_options(self) -> None:
        """Update language dropdown based on selected model"""
        model_config = self.TTS_MODELS[self.selected_model]
        supported_langs = model_config["languages"]
        
        # Update language select
        language_select = self.query_one("#language-select", Select)
        
        # If current language not supported, switch to first available
        if self.selected_language not in supported_langs:
            self.selected_language = supported_langs[0]
            language_select.value = self.selected_language
        
        # Could also disable unsupported options
        log = self.query_one("#tts-log", RichLog)
        log.write(f"[dim]Model supports: {', '.join(supported_langs)}[/dim]")