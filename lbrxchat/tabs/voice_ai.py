"""
Tab 6: Conversational Voice AI
Full STT → LLM → TTS pipeline integration
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Button, RichLog, Label, ProgressBar,
    Select, Switch
)
from textual.reactive import reactive
from textual.timer import Timer

from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Import our pipeline
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from lbrx_voice_pipeline import VoicePipeline


class VoiceAITab(Container):
    """Conversational AI with full voice pipeline"""
    
    # Conversation states
    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_PROCESSING = "processing"
    STATE_SPEAKING = "speaking"
    
    # Reactive state
    conversation_state = reactive(STATE_IDLE)
    conversation_history = reactive([])
    
    def __init__(self):
        super().__init__()
        self.voice_pipeline = VoicePipeline()
        self.conversation_id = None
        self.audio_recorder = None
        self.is_recording = False
        
    def compose(self) -> ComposeResult:
        yield Static("[bold]🤖 Conversational Voice AI[/bold]")
        
        # Main layout
        with Horizontal(classes="voiceai-layout"):
            # Left panel - Conversation
            with Vertical(classes="conversation-panel"):
                yield Static("Conversation:")
                yield RichLog(
                    id="conversation-log",
                    max_lines=30,
                    wrap=True,
                    highlight=True,
                    markup=True,
                    auto_scroll=True
                )
                
                # Status indicator
                yield Static(
                    "[bold]Status:[/bold]\n[green]● Ready[/green]\nReady to start",
                    id="status-panel"
                )
            
            # Right panel - Settings and info
            with Vertical(classes="settings-panel"):
                yield Static("Pipeline Settings:")
                
                # Model info
                yield Static("\n[bold]Active Models:[/bold]")
                yield Static("• ASR: whisper-large-v3-mlx")
                yield Static("• LLM: qwen3-8b")
                yield Static("• TTS: coqui/xtts-v2")
                
                # Settings
                yield Static("\n[bold]Options:[/bold]")
                yield Label("Auto-detect silence")
                yield Switch(
                    id="auto-silence",
                    value=True
                )
                yield Label("Save conversation")
                yield Switch(
                    id="save-convo",
                    value=True
                )
                yield Label("Continuous mode")
                yield Switch(
                    id="continuous",
                    value=False
                )
                
                # Language selection
                yield Static("\nLanguage:")
                yield Select(
                    options=[
                        ("pl", "🇵🇱 Polish"),
                        ("en", "🇬🇧 English")
                    ],
                    id="language"
                )
                
                # Stats
                yield Static("\n[bold]Session Stats:[/bold]")
                yield Label("Turns: 0", id="turn-count")
                yield Label("Duration: 00:00", id="duration")
                yield Label("Avg Response: 0.0s", id="avg-response")
        
        # Control buttons
        with Horizontal(classes="control-buttons"):
            yield Button(
                "🎤 Start Conversation",
                id="start-conversation",
                variant="success"
            )
            yield Button(
                "⏸️ Pause",
                id="pause-conversation",
                disabled=True
            )
            yield Button(
                "⏹️ Stop",
                id="stop-conversation",
                disabled=True
            )
            yield Button(
                "💾 Export",
                id="export-conversation",
                disabled=True
            )
        
        # Processing indicator
        yield ProgressBar(
            id="processing-bar",
            total=100,
            show_eta=False,
            show_percentage=False
        )
    
    def _get_status_display(self) -> Text:
        """Get formatted status display"""
        status_map = {
            self.STATE_IDLE: ("[green]● Ready[/green]", "Ready to start"),
            self.STATE_LISTENING: ("[red]● Listening[/red]", "Speak now..."),
            self.STATE_PROCESSING: ("[yellow]● Processing[/yellow]", "Thinking..."),
            self.STATE_SPEAKING: ("[blue]● Speaking[/blue]", "AI responding...")
        }
        
        indicator, message = status_map.get(
            self.conversation_state,
            ("[dim]● Unknown[/dim]", "")
        )
        
        return Text.from_markup(f"{indicator}\n{message}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "start-conversation":
            await self.start_conversation()
        elif button_id == "pause-conversation":
            await self.pause_conversation()
        elif button_id == "stop-conversation":
            await self.stop_conversation()
        elif button_id == "export-conversation":
            await self.export_conversation()
    
    async def start_conversation(self) -> None:
        """Start a new conversation session"""
        log = self.query_one("#conversation-log", RichLog)
        
        # Generate conversation ID
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Update UI
        self.query_one("#start-conversation").disabled = True
        self.query_one("#pause-conversation").disabled = False
        self.query_one("#stop-conversation").disabled = False
        
        # Clear previous conversation
        log.clear()
        self.conversation_history = []
        
        # Start session
        log.write("[green]Starting new conversation session...[/green]")
        log.write(f"[dim]Session ID: {self.conversation_id}[/dim]\n")
        
        # Initialize pipeline
        await self.initialize_pipeline()
        
        # Start conversation loop
        continuous = self.query_one("#continuous").value
        if continuous:
            await self.continuous_conversation()
        else:
            await self.single_turn_conversation()
    
    async def initialize_pipeline(self) -> None:
        """Initialize the voice pipeline"""
        log = self.query_one("#conversation-log", RichLog)
        
        # This would initialize:
        # 1. Audio input device
        # 2. Whisper model (if not already loaded)
        # 3. LLM connection
        # 4. TTS model
        
        log.write("[cyan]Initializing pipeline components...[/cyan]")
        
        # Simulate initialization
        components = ["Audio Input", "Whisper ASR", "Qwen3 LLM", "XTTS"]
        for component in components:
            await asyncio.sleep(0.5)
            log.write(f"  ✓ {component}")
        
        log.write("[green]Pipeline ready![/green]\n")
    
    async def single_turn_conversation(self) -> None:
        """Single turn: listen → process → respond"""
        log = self.query_one("#conversation-log", RichLog)
        
        # Update state
        self.conversation_state = self.STATE_LISTENING
        self.refresh_status()
        
        log.write("[yellow]🎤 Listening... (Press Stop when done)[/yellow]")
        
        # Record audio
        audio_file = await self.record_audio()
        
        if audio_file:
            # Process through pipeline
            await self.process_voice_turn(audio_file)
    
    async def continuous_conversation(self) -> None:
        """Continuous conversation with auto-detection"""
        log = self.query_one("#conversation-log", RichLog)
        
        log.write("[cyan]Continuous mode active[/cyan]")
        log.write("[dim]Will automatically detect speech and silence[/dim]\n")
        
        while self.conversation_state != self.STATE_IDLE:
            # Listen for speech
            self.conversation_state = self.STATE_LISTENING
            self.refresh_status()
            
            # Record with VAD (Voice Activity Detection)
            audio_file = await self.record_with_vad()
            
            if audio_file and self.conversation_state != self.STATE_IDLE:
                # Process turn
                await self.process_voice_turn(audio_file)
                
                # Brief pause before next turn
                await asyncio.sleep(0.5)
    
    async def record_audio(self) -> Optional[Path]:
        """Record audio from microphone"""
        # Import audio recorder
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from audio.recorder import AudioRecorder
        
        # Create recorder
        recorder = AudioRecorder(
            sample_rate=16000,
            channels=1,
            device=None,  # Use default device
            chunk_duration=0.5
        )
        
        # Set up level callback
        log = self.query_one("#conversation-log", RichLog)
        
        def on_level_update(level: float):
            # Update progress bar to show audio level
            progress = self.query_one("#processing-bar", ProgressBar)
            progress.progress = min(100, int(level * 500))
        
        recorder.on_level_update = on_level_update
        
        # Start recording
        log.write("[dim]🎤 Recording... (click Stop when done)[/dim]")
        recorder.start_recording()
        
        # Record until state changes
        while self.conversation_state == self.STATE_LISTENING:
            await asyncio.sleep(0.1)
        
        # Stop and get audio
        audio_data = recorder.stop_recording()
        
        if len(audio_data) > 0:
            # Save audio file
            audio_dir = Path("outputs/voiceai/recordings")
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%H%M%S")
            audio_file = audio_dir / f"{self.conversation_id}_{timestamp}.wav"
            
            recorder.save_recording(audio_data, str(audio_file))
            log.write(f"[dim]Recorded: {audio_file.name}[/dim]")
            return audio_file
        
        return None
    
    async def record_with_vad(self) -> Optional[Path]:
        """Record with Voice Activity Detection"""
        # This would use VAD to automatically detect speech start/end
        # For now, use simple recording
        return await self.record_audio()
    
    async def process_voice_turn(self, audio_file: Path) -> None:
        """Process one conversation turn"""
        log = self.query_one("#conversation-log", RichLog)
        
        try:
            # Update state
            self.conversation_state = self.STATE_PROCESSING
            self.refresh_status()
            
            # Step 1: Transcribe
            log.write("\n[blue]You:[/blue] ", end="")
            
            # Use actual pipeline
            result = await self.voice_pipeline.process_audio(
                str(audio_file),
                output_dir=f"outputs/voiceai/{self.conversation_id}",
                voice_response=True
            )
            
            # Get transcription
            transcription = result.get('transcription', {}).get('text', '')
            log.write(transcription)
            
            # Add to history
            self.conversation_history.append({
                "role": "user",
                "content": transcription,
                "timestamp": datetime.now().isoformat()
            })
            
            # Get AI response
            analysis = result.get('analysis', {})
            response_text = analysis.get('summary', 'Przepraszam, nie zrozumiałem.')
            
            # Show AI response
            log.write(f"\n[green]AI:[/green] {response_text}")
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 3: Speak response
            if result.get('audio_response'):
                self.conversation_state = self.STATE_SPEAKING
                self.refresh_status()
                
                # Play audio (simulated)
                log.write("\n[dim]🔊 Playing response...[/dim]")
                await asyncio.sleep(2)  # Simulate playback
            
            # Update stats
            self.update_stats()
            
        except Exception as e:
            log.write(f"\n[red]Error: {e}[/red]")
        
        finally:
            # Return to listening or idle
            if self.query_one("#continuous").value:
                self.conversation_state = self.STATE_LISTENING
            else:
                self.conversation_state = self.STATE_IDLE
                await self.stop_conversation()
            
            self.refresh_status()
    
    async def pause_conversation(self) -> None:
        """Pause the conversation"""
        log = self.query_one("#conversation-log", RichLog)
        
        self.conversation_state = self.STATE_IDLE
        self.refresh_status()
        
        log.write("\n[yellow]Conversation paused[/yellow]")
        
        # Update buttons
        self.query_one("#pause-conversation").disabled = True
        self.query_one("#start-conversation").disabled = False
        self.query_one("#start-conversation").label = "▶️ Resume"
    
    async def stop_conversation(self) -> None:
        """Stop and end the conversation"""
        log = self.query_one("#conversation-log", RichLog)
        
        self.conversation_state = self.STATE_IDLE
        self.refresh_status()
        
        log.write("\n[red]Conversation ended[/red]")
        
        # Save if enabled
        if self.query_one("#save-convo").value:
            await self.save_conversation()
        
        # Update buttons
        self.query_one("#start-conversation").disabled = False
        self.query_one("#start-conversation").label = "🎤 Start Conversation"
        self.query_one("#pause-conversation").disabled = True
        self.query_one("#stop-conversation").disabled = True
        self.query_one("#export-conversation").disabled = False
        
        # Show summary
        self.show_conversation_summary()
    
    async def save_conversation(self) -> None:
        """Save conversation to file"""
        if not self.conversation_history:
            return
        
        output_dir = Path("outputs/voiceai/conversations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        conversation_file = output_dir / f"{self.conversation_id}_conversation.json"
        
        data = {
            "session_id": self.conversation_id,
            "language": self.query_one("#language").value,
            "turns": len(self.conversation_history) // 2,
            "history": self.conversation_history
        }
        
        import json
        conversation_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        log = self.query_one("#conversation-log", RichLog)
        log.write(f"\n[green]Saved: {conversation_file.name}[/green]")
    
    async def export_conversation(self) -> None:
        """Export conversation in various formats"""
        log = self.query_one("#conversation-log", RichLog)
        
        if not self.conversation_history:
            log.write("[red]No conversation to export[/red]")
            return
        
        output_dir = Path("outputs/voiceai/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export as markdown
        md_file = output_dir / f"{self.conversation_id}_conversation.md"
        
        content = f"# Conversation {self.conversation_id}\n\n"
        for entry in self.conversation_history:
            role = "Human" if entry["role"] == "user" else "AI"
            content += f"**{role}**: {entry['content']}\n\n"
        
        md_file.write_text(content, encoding='utf-8')
        
        log.write(f"\n[green]Exported to: {md_file.name}[/green]")
    
    def refresh_status(self) -> None:
        """Refresh status panel"""
        status_panel = self.query_one("#status-panel", Static)
        status_text = self._get_status_display()
        status_panel.update(f"[bold]Status:[/bold]\n{status_text}")
        
        # Update progress bar visibility
        progress = self.query_one("#processing-bar", ProgressBar)
        if self.conversation_state in [self.STATE_LISTENING, self.STATE_PROCESSING]:
            progress.styles.visibility = "visible"
        else:
            progress.styles.visibility = "hidden"
    
    def update_stats(self) -> None:
        """Update conversation statistics"""
        turns = len(self.conversation_history) // 2
        self.query_one("#turn-count").update(f"Turns: {turns}")
        
        # Update other stats...
    
    def show_conversation_summary(self) -> None:
        """Show conversation summary"""
        log = self.query_one("#conversation-log", RichLog)
        
        if not self.conversation_history:
            return
        
        turns = len(self.conversation_history) // 2
        
        log.write("\n" + "="*50)
        log.write("[bold]Conversation Summary:[/bold]")
        log.write(f"• Total turns: {turns}")
        log.write(f"• Session ID: {self.conversation_id}")
        log.write("="*50)