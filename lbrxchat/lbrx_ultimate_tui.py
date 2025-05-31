#!/usr/bin/env python3
"""
lbrxChat Ultimate - 6-Tab Audio/Voice/AI Platform
=================================================

Complete audio-text-voice processing platform in a single TUI.
Integrates all existing components into a unified interface.

(c)2025 M&K
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Textual imports
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Header, Footer, TabbedContent, TabPane,
    Button, Static, Input, Label, RichLog,
    DataTable, ProgressBar, Select
)
from textual.reactive import reactive

# Rich for formatting
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing components
from tools.whisper_config import WhisperConfig
from lbrx_voice_pipeline import VoicePipeline

# Import tab components
from lbrxchat.tabs.transcribe_files import TranscribeFilesTab
from lbrxchat.tabs.transcribe_voice import TranscribeVoiceTab
from lbrxchat.tabs.tts import TTSTab
from lbrxchat.tabs.voice_ai import VoiceAITab

# Server clients
import httpx
import websockets


class LbrxUltimateTUI(App):
    """Main TUI application with 6 tabs"""
    
    CSS = """
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 1;
    }
    
    .tab-content {
        height: 100%;
        overflow-y: auto;
    }
    
    DataTable {
        height: 80%;
    }
    
    RichLog {
        border: solid green;
        height: 100%;
    }
    
    Input {
        margin: 1 0;
    }
    
    Button {
        margin: 1 0;
    }
    
    ProgressBar {
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("f1", "switch_tab('chat')", "Chat"),
        Binding("f2", "switch_tab('rag')", "RAG"),
        Binding("f3", "switch_tab('files')", "Files"),
        Binding("f4", "switch_tab('voice')", "Voice"),
        Binding("f5", "switch_tab('tts')", "TTS"),
        Binding("f6", "switch_tab('voiceai')", "VoiceAI"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "lbrxChat Ultimate"
        
        # Initialize components
        self.whisper_config = WhisperConfig.polish_optimized()
        self.voice_pipeline = VoicePipeline()
        self.http_client = httpx.AsyncClient()
        
        # Server endpoints
        self.whisper_batch_url = "http://localhost:8123"
        self.whisper_ws_url = "ws://localhost:8126/v1/audio/transcriptions"
        self.tts_dia_url = "http://localhost:8124"
        self.tts_csm_url = "http://localhost:8125"
        
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header()
        
        with TabbedContent(initial="chat"):
            # Tab 1: Chat
            with TabPane("Chat [F1]", id="chat"):
                yield ChatTab()
            
            # Tab 2: RAG Manager
            with TabPane("RAG [F2]", id="rag"):
                yield RAGTab()
            
            # Tab 3: Transcribe Files
            with TabPane("Files [F3]", id="files"):
                yield TranscribeFilesTab()
            
            # Tab 4: Transcribe Voice
            with TabPane("Voice [F4]", id="voice"):
                yield TranscribeVoiceTab()
            
            # Tab 5: TTS
            with TabPane("TTS [F5]", id="tts"):
                yield TTSTab()
            
            # Tab 6: VoiceAI
            with TabPane("VoiceAI [F6]", id="voiceai"):
                yield VoiceAITab()
        
        yield Footer()
    
    def action_switch_tab(self, tab_name: str) -> None:
        """Switch to specified tab"""
        self.query_one(TabbedContent).active = tab_name


class ChatTab(Container):
    """Tab 1: Existing chat functionality"""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]💬 Chat with LLM[/bold]", classes="tab-title")
        yield RichLog(id="chat-log", classes="tab-content")
        yield Input(placeholder="Type your message...", id="chat-input")
        yield Button("Send", id="chat-send", variant="primary")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "chat-send":
            await self.send_message()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            await self.send_message()
    
    async def send_message(self) -> None:
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value
        if not message:
            return
            
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[blue]You:[/blue] {message}")
        input_widget.value = ""
        
        # Call LM Studio
        try:
            log.write("[yellow]AI:[/yellow] [dim]Thinking...[/dim]")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:1234/v1/chat/completions",
                    json={
                        "model": "qwen3-8b-mlx",
                        "messages": [
                            {"role": "system", "content": "You are a helpful AI assistant. Be concise."},
                            {"role": "user", "content": message}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                        "stream": True
                    }
                )
                
                if response.status_code == 200:
                    # Clear thinking message and show input
                    log.clear()
                    log.write(f"[blue]You:[/blue] {message}")
                    
                    # Stream response
                    ai_message = ""
                    log.write(f"[yellow]AI:[/yellow] ", end="")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            
                            try:
                                import json
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        ai_message += content
                                        # Update the log with streaming text
                                        log.clear()
                                        log.write(f"[blue]You:[/blue] {message}")
                                        log.write(f"[yellow]AI:[/yellow] {ai_message}")
                            except:
                                continue
                    
                    # Add final touch for Polish projects
                    if ai_message and not ai_message.endswith("No i zajebiście!"):
                        ai_message += "\n\nNo i zajebiście!"
                        log.clear()
                        log.write(f"[blue]You:[/blue] {message}")
                        log.write(f"[yellow]AI:[/yellow] {ai_message}")
                        
                else:
                    log.write(f"[red]Error:[/red] LM Studio returned {response.status_code}")
                    
        except Exception as e:
            log.write(f"[red]Error:[/red] {str(e)}")


class RAGTab(Container):
    """Tab 2: RAG knowledge base management"""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]📚 RAG Knowledge Base Manager[/bold]", classes="tab-title")
        
        with Horizontal():
            with Container(classes="rag-list"):
                yield Static("Knowledge Bases:")
                yield DataTable(id="rag-table")
            
            with Container(classes="rag-actions"):
                yield Button("Add Graph", id="rag-add")
                yield Button("Remove Graph", id="rag-remove")
                yield Button("Import JSONL", id="rag-import")
                yield Button("Export JSONL", id="rag-export")
    
    def on_mount(self) -> None:
        table = self.query_one("#rag-table", DataTable)
        table.add_columns("Name", "Documents", "Status")
        
        # Sample data
        table.add_row("MLX Documentation", "1,234", "✅ Active")
        table.add_row("Veterinary (Merck)", "5,678", "✅ Active")
        table.add_row("Whisper Tricks", "456", "⏸️ Inactive")




def main():
    """Run the application"""
    app = LbrxUltimateTUI()
    app.run()


if __name__ == "__main__":
    main()