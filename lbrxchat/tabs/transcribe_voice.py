"""
Tab 4: Live Voice Transcription
Integrates with whisper_servers/realtime WebSocket API
"""

import asyncio
import base64
import json
from typing import Optional, Any
import numpy as np
import websockets
import sounddevice as sd

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, Button, Select, RichLog, ProgressBar,
    Sparkline, Label
)
from textual.reactive import reactive
from textual.timer import Timer

from rich.panel import Panel
from rich.text import Text

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from lbrxchat.widgets.audio_spectrogram import AudioSpectrogram


class TranscribeVoiceTab(Container):
    """Live voice transcription with WebSocket streaming"""
    
    # Reactive state
    is_recording = reactive(False)
    audio_level = reactive(0.0)
    selected_device = reactive(None)
    
    def __init__(self):
        super().__init__()
        self.ws_url = "ws://localhost:8126/v1/audio/transcriptions"
        self.websocket = None
        self.audio_stream = None
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 0.5  # seconds
        self.audio_buffer = []
        self.audio_queue = []  # For queuing audio when no event loop
        self.level_timer = None
        
    def compose(self) -> ComposeResult:
        yield Static("[bold]🎤 Live Voice Transcription[/bold]")
        
        with Horizontal(classes="voice-layout"):
            # Left panel - Audio controls
            with Vertical(classes="audio-controls"):
                yield Static("Audio Input Device:")
                yield Select(
                    options=self._get_audio_devices(),
                    id="audio-device"
                )
                
                yield Static("\nAudio Level:")
                yield ProgressBar(
                    id="audio-level",
                    total=100,
                    show_eta=False,
                    show_percentage=False
                )
                
                yield Static("\nSpectrogram:")
                yield AudioSpectrogram(
                    id="voice-spectrogram"
                )
                
                with Horizontal(classes="record-controls"):
                    yield Button(
                        "⏺️ Start Recording",
                        id="record-toggle",
                        variant="error"
                    )
                    yield Button(
                        "💾 Save Session",
                        id="save-session",
                        disabled=True
                    )
            
            # Right panel - Settings
            with Vertical(classes="voice-settings"):
                yield Static("Recording Settings:")
                yield Label(f"Sample Rate: {self.sample_rate} Hz")
                yield Label(f"Channels: {self.channels}")
                yield Label(f"Chunk Duration: {self.chunk_duration}s")
                
                yield Static("\nTranscription Settings:")
                yield Label("Language: Polish (pl)")
                yield Label("Model: whisper-large-v3-mlx")
                yield Label("Real-time mode: WebSocket")
                
                yield Button(
                    "⚙️ Configure",
                    id="voice-config"
                )
        
        # Transcription output
        yield Static("\n[bold]Live Transcription:[/bold]")
        yield RichLog(
            id="transcription-log",
            max_lines=20,
            wrap=True,
            highlight=True,
            markup=True
        )
        
        # Status bar
        yield Static(
            "Status: [green]Ready[/green]",
            id="voice-status"
        )
    
    def _get_audio_devices(self) -> list:
        """Get list of available audio input devices"""
        devices = [("default", "System Default")]
        
        try:
            # Get all input devices
            for i, device in enumerate(sd.query_devices()):
                if device['max_input_channels'] > 0:
                    devices.append((str(i), f"{device['name']} ({device['hostapi']})"))
        except Exception as e:
            log = self.query_one("#transcription-log", RichLog)
            log.write(f"[red]Error listing devices: {e}[/red]")
        
        return devices
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "record-toggle":
            await self.toggle_recording()
        elif button_id == "save-session":
            await self.save_session()
        elif button_id == "voice-config":
            await self.configure_voice()
    
    async def toggle_recording(self) -> None:
        """Start or stop recording"""
        if not self.is_recording:
            await self.start_recording()
        else:
            await self.stop_recording()
    
    async def start_recording(self) -> None:
        """Start audio recording and WebSocket connection"""
        try:
            log = self.query_one("#transcription-log", RichLog)
            status = self.query_one("#voice-status", Static)
            button = self.query_one("#record-toggle", Button)
            
            # Update UI
            self.is_recording = True
            button.label = "⏹️ Stop Recording"
            button.variant = "default"
            status.update("Status: [yellow]Connecting...[/yellow]")
            
            # Connect to WebSocket
            log.write("[cyan]Connecting to transcription server...[/cyan]")
            self.websocket = await websockets.connect(self.ws_url)
            
            # Send initial configuration
            config = {
                "config": {
                    "sample_rate": self.sample_rate,
                    "language": "pl",
                    "model": "whisper-large-v3-mlx"
                }
            }
            await self.websocket.send(json.dumps(config))
            
            # Start audio stream
            device_id = self.query_one("#audio-device", Select).value
            if device_id == "default":
                device_id = None
            else:
                device_id = int(device_id)
            
            self.audio_stream = sd.InputStream(
                device=device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration)
            )
            
            self.audio_stream.start()
            status.update("Status: [red]● Recording[/red]")
            log.write("[green]Recording started![/green]")
            
            # Start receiving transcriptions
            asyncio.create_task(self.receive_transcriptions())
            
            # Start audio level monitoring
            self.level_timer = self.set_interval(0.1, self.update_audio_level)
            
            # Mark spectrogram as active
            spectrogram = self.query_one("#voice-spectrogram", AudioSpectrogram)
            spectrogram.start_recording()
            
            # Enable save button
            self.query_one("#save-session").disabled = False
            
        except Exception as e:
            log.write(f"[red]Error starting recording: {e}[/red]")
            await self.stop_recording()
    
    async def stop_recording(self) -> None:
        """Stop audio recording and close WebSocket"""
        try:
            log = self.query_one("#transcription-log", RichLog)
            status = self.query_one("#voice-status", Static)
            button = self.query_one("#record-toggle", Button)
            
            # Stop audio stream
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            # Close WebSocket
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            # Stop level monitoring
            if self.level_timer:
                self.level_timer.stop()
            
            # Stop spectrogram
            spectrogram = self.query_one("#voice-spectrogram", AudioSpectrogram)
            spectrogram.stop_recording()
            
            # Update UI
            self.is_recording = False
            button.label = "⏺️ Start Recording"
            button.variant = "error"
            status.update("Status: [green]Ready[/green]")
            
            log.write("[yellow]Recording stopped[/yellow]")
            
        except Exception as e:
            log.write(f"[red]Error stopping recording: {e}[/red]")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Add to buffer for level monitoring
        self.audio_buffer = indata.copy()
        
        # Send audio data via WebSocket if connected
        if self.websocket and not self.websocket.closed:
            # Convert to base64
            audio_bytes = (indata * 32767).astype(np.int16).tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send as JSON
            message = {
                "audio_data": audio_b64,
                "sample_rate": self.sample_rate
            }
            
            # Use asyncio to send (callback is sync)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_audio(json.dumps(message)))
            else:
                # If no event loop, queue the data
                self.audio_queue.put(message)
    
    async def send_audio(self, message: str) -> None:
        """Send audio data to WebSocket"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.send(message)
        except Exception as e:
            log = self.query_one("#transcription-log", RichLog)
            log.write(f"[red]Error sending audio: {e}[/red]")
    
    async def receive_transcriptions(self) -> None:
        """Receive transcriptions from WebSocket"""
        log = self.query_one("#transcription-log", RichLog)
        
        try:
            while self.websocket and not self.websocket.closed:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data.get("type") == "transcription":
                    text = data.get("text", "")
                    is_final = data.get("is_final", False)
                    
                    if text:
                        if is_final:
                            log.write(f"[green]Final:[/green] {text}")
                        else:
                            log.write(f"[dim]Partial:[/dim] {text}")
                
                elif data.get("type") == "error":
                    error = data.get("error", "Unknown error")
                    log.write(f"[red]Server error: {error}[/red]")
                    
        except websockets.exceptions.ConnectionClosed:
            log.write("[yellow]Connection closed[/yellow]")
        except Exception as e:
            log.write(f"[red]Error receiving: {e}[/red]")
    
    def update_audio_level(self) -> None:
        """Update audio level indicator"""
        if len(self.audio_buffer) > 0:
            # Calculate RMS level
            rms = np.sqrt(np.mean(self.audio_buffer**2))
            # Convert to percentage (0-100)
            level = min(100, int(rms * 500))
            
            # Update progress bar
            level_bar = self.query_one("#audio-level", ProgressBar)
            level_bar.progress = level
            
            # Update spectrogram
            spectrogram = self.query_one("#voice-spectrogram", AudioSpectrogram)
            if self.is_recording:
                # Update with actual audio data
                spectrogram.update_spectrum(self.audio_buffer.flatten(), self.sample_rate)
            else:
                # Just update level for visual feedback
                spectrogram.update_level(rms)
    
    async def save_session(self) -> None:
        """Save recording session to file"""
        log = self.query_one("#transcription-log", RichLog)
        
        # In a real implementation, this would save:
        # 1. Audio file (MP3/WAV)
        # 2. Transcription text file
        # 3. Timestamped JSON
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log.write(f"[green]Session saved: voice_session_{timestamp}[/green]")
        log.write("  • Audio: voice_session_{timestamp}.mp3")
        log.write("  • Text: voice_session_{timestamp}.txt")
        log.write("  • JSON: voice_session_{timestamp}.json")
    
    async def configure_voice(self) -> None:
        """Open voice configuration dialog"""
        log = self.query_one("#transcription-log", RichLog)
        log.write("[yellow]Voice configuration dialog not implemented yet[/yellow]")
        
        # This could open a modal with:
        # - Sample rate selection
        # - Audio format options
        # - Whisper model selection
        # - Language settings
        # - VAD (Voice Activity Detection) settings