#!/usr/bin/env python3
"""
TUI Dashboard for MLX Whisper server.
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List
import subprocess

import requests
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, DataTable, Label, Input, RadioSet, RadioButton
from textual.reactive import reactive
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class JobsTable(Static):
    """Widget for displaying transcription jobs."""
    
    jobs = reactive([])
    
    def __init__(self, server_url="http://localhost:8123"):
        super().__init__()
        self.server_url = server_url
    
    def on_mount(self):
        # Schedule the first refresh immediately
        self.refresh_jobs()
        # Then schedule to refresh every 2 seconds
        self.set_interval(2, self.refresh_jobs)
    
    def refresh_jobs(self):
        """Refresh the jobs list."""
        try:
            response = requests.get(f"{self.server_url}/v1/jobs")
            if response.status_code == 200:
                self.jobs = response.json()
            else:
                self.jobs = []
        except Exception as e:
            self.jobs = []
    
    def render(self):
        """Render the jobs table."""
        table = Table(title="Transcription Jobs", expand=True)
        table.add_column("ID", no_wrap=True)
        table.add_column("Status", no_wrap=True)
        table.add_column("Created", no_wrap=True)
        table.add_column("Completed", no_wrap=True)
        
        for job in self.jobs:
            job_id = job["id"]
            status = job["status"]
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(job["created_at"]))
            
            if job["completed_at"]:
                completed_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(job["completed_at"]))
            else:
                completed_at = "-"
            
            # Style based on status
            if status == "completed":
                status_style = "green"
            elif status == "processing":
                status_style = "yellow"
            elif status == "failed":
                status_style = "red"
            else:
                status_style = "blue"
            
            table.add_row(
                job_id,
                Text(status, style=status_style),
                created_at,
                completed_at,
            )
        
        return Panel(table)


class TranscriptionForm(Container):
    """Form for uploading and transcribing audio files."""
    
    def __init__(self, server_url="http://localhost:8123"):
        super().__init__()
        self.server_url = server_url
    
    def compose(self) -> ComposeResult:
        yield Label("File Path:")
        yield Input(placeholder="Enter file path", id="file_path")
        
        yield Label("Model:")
        yield Input(placeholder="Model name", value="whisper-large-v3", id="model")
        
        yield Label("Language (optional):")
        yield Input(placeholder="Language code (e.g., en)", id="language")
        
        yield Label("Prompt (optional):")
        yield Input(placeholder="Prompt for the model", id="prompt")
        
        yield Horizontal(
            Button("Browse", id="browse"),
            Button("Transcribe", id="transcribe"),
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "browse":
            self.browse_file()
        elif event.button.id == "transcribe":
            self.transcribe_file()
    
    def browse_file(self) -> None:
        """Open a file dialog to select an audio file."""
        # Simple implementation using subprocess to run a system file dialog
        # In a real application, you might want to use a proper file dialog
        file_path = self.query_one("#file_path", Input)
        self.app.push_screen("file_dialog", lambda path: file_path.value = path if path else file_path.value)
    
    def transcribe_file(self) -> None:
        """Send the file for transcription."""
        file_path = self.query_one("#file_path", Input).value
        model = self.query_one("#model", Input).value
        language = self.query_one("#language", Input).value
        prompt = self.query_one("#prompt", Input).value
        
        if not file_path:
            self.app.notify("Please select a file", severity="error")
            return
        
        if not os.path.exists(file_path):
            self.app.notify(f"File not found: {file_path}", severity="error")
            return
        
        # Start transcription in a background task
        asyncio.create_task(self._transcribe_file_async(file_path, model, language, prompt))
    
    async def _transcribe_file_async(self, file_path, model, language, prompt):
        """Transcribe the file asynchronously."""
        self.app.notify(f"Transcribing {os.path.basename(file_path)}...", severity="information")
        
        # Prepare the request
        url = f"{self.server_url}/v1/audio/transcriptions"
        files = {"file": open(file_path, "rb")}
        data = {"model": model}
        
        if language:
            data["language"] = language
        
        if prompt:
            data["prompt"] = prompt
        
        # Send the request in a separate thread
        try:
            response = await asyncio.to_thread(
                requests.post, url, files=files, data=data
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Get the result
            result = response.json()
            
            # Show the result
            self.app.notify("Transcription completed successfully", severity="information")
            
            # Update the result view
            result_view = self.app.query_one("#result_view", ResultView)
            result_view.update_result(result)
            
        except Exception as e:
            self.app.notify(f"Error: {str(e)}", severity="error")


class ResultView(Static):
    """Widget for displaying transcription results."""
    
    result = reactive(None)
    
    def update_result(self, result):
        """Update the transcription result."""
        self.result = result
        self.refresh()
    
    def render(self):
        """Render the transcription result."""
        if not self.result:
            return Panel("No transcription result yet", title="Result")
        
        text = self.result.get("text", "")
        language = self.result.get("language", "unknown")
        duration = self.result.get("duration", 0)
        
        result_table = Table(expand=True)
        result_table.add_column("Transcription")
        result_table.add_row(text)
        
        info_table = Table(expand=True)
        info_table.add_column("Language")
        info_table.add_column("Duration")
        info_table.add_row(language, f"{duration:.2f} seconds")
        
        segments_table = Table(title="Segments", expand=True)
        segments_table.add_column("Start")
        segments_table.add_column("End")
        segments_table.add_column("Text")
        
        for segment in self.result.get("segments", []):
            segments_table.add_row(
                f"{segment.get('start', 0):.2f}s",
                f"{segment.get('end', 0):.2f}s",
                segment.get("text", ""),
            )
        
        return Panel(
            Vertical(
                Panel(result_table, title="Full Transcription"),
                Panel(info_table, title="Information"),
                Panel(segments_table, title="Segments"),
            ),
            title="Transcription Result",
        )


class MLXWhisperDashboard(App):
    """TUI Dashboard for MLX Whisper server."""
    
    CSS = """
    #jobs_container {
        layout: horizontal;
        height: 1fr;
    }
    
    #left_panel {
        width: 60%;
        margin: 1;
    }
    
    #right_panel {
        width: 40%;
        margin: 1;
    }
    
    #form_panel {
        height: 30%;
        margin-bottom: 1;
    }
    
    #result_panel {
        height: 70%;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Jobs"),
    ]
    
    def __init__(self, server_url="http://localhost:8123"):
        super().__init__()
        self.server_url = server_url
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        # Main container
        with Container(id="jobs_container"):
            # Left panel - Jobs table
            with Container(id="left_panel"):
                yield JobsTable(server_url=self.server_url)
            
            # Right panel - Upload form and result view
            with Container(id="right_panel"):
                # Form panel
                with Container(id="form_panel"):
                    yield TranscriptionForm(server_url=self.server_url)
                
                # Result panel
                with Container(id="result_panel"):
                    yield ResultView(id="result_view")
        
        yield Footer()
    
    def action_refresh(self) -> None:
        """Refresh the jobs list."""
        jobs_table = self.query_one(JobsTable)
        jobs_table.refresh_jobs()


def main():
    """Run the TUI dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TUI Dashboard for MLX Whisper server")
    parser.add_argument("--server", default="http://localhost:8123", help="Server URL (default: http://localhost:8123)")
    args = parser.parse_args()
    
    app = MLXWhisperDashboard(server_url=args.server)
    app.run()


if __name__ == "__main__":
    main()
