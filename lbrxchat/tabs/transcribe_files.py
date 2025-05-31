"""
Tab 3: Batch File Transcription
Integrates with existing whisper_servers/batch API
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import httpx
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, DataTable, Button, ProgressBar, 
    Checkbox, RichLog
)
from textual.reactive import reactive

from tools.whisper_config import WhisperConfig


class TranscribeFilesTab(Container):
    """Enhanced batch transcription tab with full integration"""
    
    # Reactive state
    selected_files = reactive([])
    output_formats = reactive({
        "txt": True,
        "timestamped": False,
        "word_timestamped": True,
        "markdown": False,
        "json": True
    })
    
    def __init__(self):
        super().__init__()
        self.whisper_config = WhisperConfig.polish_optimized()
        self.http_client = httpx.AsyncClient()
        self.batch_api_url = "http://localhost:8123"
        self.active_jobs = {}
        
    def compose(self) -> ComposeResult:
        yield Static("[bold]📁 Batch File Transcription[/bold]")
        
        with Horizontal(classes="transcribe-layout"):
            # Left panel - File list
            with Vertical(classes="files-panel"):
                yield Static("Input Files:")
                yield DataTable(id="files-table", zebra_stripes=True)
                
                with Horizontal():
                    yield Button("Add Files", id="add-files", variant="primary")
                    yield Button("Clear All", id="clear-files")
                    yield Button("Remove Selected", id="remove-selected")
            
            # Right panel - Settings
            with Vertical(classes="settings-panel"):
                yield Static("Output Formats:")
                
                # Format checkboxes
                yield Checkbox("Plain text (.txt)", id="fmt-txt", value=True)
                yield Checkbox("Timestamped", id="fmt-timestamped")
                yield Checkbox("Word-timestamped", id="fmt-word", value=True)
                yield Checkbox("Markdown (.md)", id="fmt-markdown")
                yield Checkbox("JSON (.json)", id="fmt-json", value=True)
                
                yield Static("\nWhisper Settings:")
                yield Static(f"Model: {self.whisper_config.model_name.split('/')[-1]}")
                yield Static(f"Language: {self.whisper_config.language}")
                yield Button("Configure Whisper", id="config-whisper")
        
        # Progress section
        yield Static("\nProgress:")
        yield ProgressBar(id="batch-progress", total=100, show_eta=True)
        yield RichLog(id="batch-log", max_lines=10)
        
        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("Start Transcription", id="start-batch", variant="success")
            yield Button("Pause", id="pause-batch", disabled=True)
            yield Button("Cancel", id="cancel-batch", disabled=True)
    
    def on_mount(self) -> None:
        """Initialize the file table"""
        table = self.query_one("#files-table", DataTable)
        table.add_columns("☑", "Filename", "Size", "Duration", "Status")
        table.cursor_type = "row"
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "add-files":
            await self.add_files()
        elif button_id == "clear-files":
            self.clear_files()
        elif button_id == "remove-selected":
            await self.remove_selected_files()
        elif button_id == "start-batch":
            await self.start_transcription()
        elif button_id == "config-whisper":
            await self.configure_whisper()
    
    async def add_files(self) -> None:
        """Add audio files to the batch"""
        # In a real implementation, this would open a file dialog
        # For now, let's scan the uploads directory
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
            files = [f for f in uploads_dir.iterdir() 
                    if f.suffix.lower() in audio_extensions]
            
            table = self.query_one("#files-table", DataTable)
            for file in files[:5]:  # Limit to 5 for demo
                # Get file info
                size_mb = file.stat().st_size / (1024 * 1024)
                
                # Add to table
                table.add_row(
                    "☑",
                    file.name,
                    f"{size_mb:.1f} MB",
                    "??:??",  # Duration would be calculated
                    "Ready"
                )
                
                self.selected_files.append(file)
            
            log = self.query_one("#batch-log", RichLog)
            log.write(f"[green]Added {len(files)} files[/green]")
    
    def clear_files(self) -> None:
        """Clear all files from the list"""
        table = self.query_one("#files-table", DataTable)
        table.clear()
        self.selected_files = []
        
        log = self.query_one("#batch-log", RichLog)
        log.write("[yellow]Cleared file list[/yellow]")
    
    async def remove_selected_files(self) -> None:
        """Remove selected files from the list"""
        table = self.query_one("#files-table", DataTable)
        if table.cursor_row is not None:
            # Remove from list
            if 0 <= table.cursor_row < len(self.selected_files):
                removed_file = self.selected_files.pop(table.cursor_row)
                table.remove_row(table.cursor_row)
                
                log = self.query_one("#batch-log", RichLog)
                log.write(f"[yellow]Removed {removed_file.name}[/yellow]")
    
    async def start_transcription(self) -> None:
        """Start batch transcription process"""
        if not self.selected_files:
            log = self.query_one("#batch-log", RichLog)
            log.write("[red]No files selected![/red]")
            return
        
        # Update UI
        self.query_one("#start-batch").disabled = True
        self.query_one("#pause-batch").disabled = False
        self.query_one("#cancel-batch").disabled = False
        
        log = self.query_one("#batch-log", RichLog)
        progress = self.query_one("#batch-progress", ProgressBar)
        table = self.query_one("#files-table", DataTable)
        
        total_files = len(self.selected_files)
        progress.total = total_files
        progress.progress = 0
        
        log.write(f"[cyan]Starting transcription of {total_files} files...[/cyan]")
        
        # Process each file
        for idx, file_path in enumerate(self.selected_files):
            try:
                # Update status in table
                table.update_cell(idx, 4, "Processing...")
                
                # Call Whisper API
                log.write(f"[blue]Transcribing {file_path.name}...[/blue]")
                
                # Upload file
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'audio/mpeg')}
                    data = {
                        'language': self.whisper_config.language,
                        'response_format': 'json',
                        # Add other config params
                    }
                    
                    response = await self.http_client.post(
                        f"{self.batch_api_url}/v1/audio/transcriptions",
                        files=files,
                        data=data
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    job_id = result.get('job_id')
                    
                    # Track job
                    self.active_jobs[job_id] = {
                        'file': file_path,
                        'status': 'processing',
                        'row': idx
                    }
                    
                    # Update table
                    table.update_cell(idx, 4, f"Job: {job_id[:8]}...")
                    
                    # Save outputs based on selected formats
                    await self.save_transcription_outputs(file_path, result)
                    
                else:
                    log.write(f"[red]Error: {response.status_code}[/red]")
                    table.update_cell(idx, 4, "Failed")
                
                # Update progress
                progress.progress = idx + 1
                
            except Exception as e:
                log.write(f"[red]Error processing {file_path.name}: {e}[/red]")
                table.update_cell(idx, 4, "Error")
        
        # Reset UI
        self.query_one("#start-batch").disabled = False
        self.query_one("#pause-batch").disabled = True
        self.query_one("#cancel-batch").disabled = True
        
        log.write("[green]Batch transcription completed![/green]")
    
    async def save_transcription_outputs(self, file_path: Path, result: Dict) -> None:
        """Save transcription in selected formats"""
        output_dir = Path("outputs/batch") / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = file_path.stem
        
        # Get transcription text
        text = result.get('text', '')
        
        # Save based on selected formats
        if self.output_formats["txt"]:
            (output_dir / f"{base_name}.txt").write_text(text, encoding='utf-8')
        
        if self.output_formats["json"]:
            import json
            (output_dir / f"{base_name}.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        
        # TODO: Implement other formats (timestamped, word-level, markdown)
        
        log = self.query_one("#batch-log", RichLog)
        log.write(f"[green]Saved outputs to {output_dir}[/green]")
    
    async def configure_whisper(self) -> None:
        """Open Whisper configuration dialog"""
        # This could open a modal or switch to a config screen
        log = self.query_one("#batch-log", RichLog)
        log.write("[yellow]Whisper configuration not implemented yet[/yellow]")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Update output format selection"""
        checkbox_id = event.checkbox.id
        format_map = {
            "fmt-txt": "txt",
            "fmt-timestamped": "timestamped",
            "fmt-word": "word_timestamped",
            "fmt-markdown": "markdown",
            "fmt-json": "json"
        }
        
        if checkbox_id in format_map:
            format_key = format_map[checkbox_id]
            self.output_formats[format_key] = event.checkbox.value