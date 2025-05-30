#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LBRXCHAT TUI Interface
======================

A sophisticated TUI-based interface for LBRXCHAT, powered by Textual.
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import (
    Header, Footer, Button, Static, Input, Label,
    Select, RichLog
)
from textual.reactive import reactive
from textual.binding import Binding

# Import core components
from lbrxchat.core.models import MLXModelManager
from lbrxchat.core.rag import VetRAGSystem
from lbrxchat.core.config import (
    PROJECT_ROOT, INDEX_PATH, INDEX_FILE, 
    DEFAULT_LLM_MODEL, SYSTEM_PROMPTS
)

# === TUI Application ===
class ChatApp(App):
    """TUI application for LBRXCHAT RAG QA system"""
    
    TITLE = "LBRXCHAT - LIBRAXIS Advanced Chat Framework"
    SUB_TITLE = "Powered by MLX and Textual"
    
    CSS_PATH = str(PROJECT_ROOT / "lbrxchat" / "ui" / "styles.css")
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reload_index", "Reload Index"),
        Binding("c", "clear_chat", "Clear Chat"),
        Binding("m", "change_model", "Change Model"),
    ]
    
    def __init__(self):
        super().__init__()
        self.model_manager = MLXModelManager()
        self.rag_system = VetRAGSystem(self.model_manager)
        self.available_models = self.model_manager.get_available_models()
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        # Create header
        yield Header()
        
        # Main layout
        with Container(id="app-grid"):
            # Left panel - Settings and Info
            with Container(id="left-panel"):
                yield Label("Models", id="models-header")
                yield Select(
                    [(model, model) for model in self.available_models],
                    id="model-selector",
                    value=DEFAULT_LLM_MODEL,
                    prompt="Select LLM Model"
                )
                
                yield Button("Build/Reload Index", id="build-index-btn")
                yield Button("Clear Chat", id="clear-chat-btn")
                
                yield Label("System Information", id="system-info-header")
                yield Static(id="system-info")
                
                # Progress bar for loading
                yield Static("", id="progress-label")
                yield Static("", id="progress-bar")
            
            # Right panel - Chat and Results
            with Container(id="right-panel"):
                # Chat history
                yield RichLog(id="chat-log", markup=True, highlight=True)
                
                # Input area
                with Container(id="input-container"):
                    yield Input(placeholder="Ask a question...", id="query-input")
                    yield Button("Send", id="send-btn")
        
        # Footer
        yield Footer()
    
    def on_mount(self) -> None:
        """When app is mounted (started)"""
        # Update system info
        self.update_system_info()
        
        # Load index if exists
        self.load_index_async()
    
    def update_system_info(self) -> None:
        """Update system information display"""
        info_widget = self.query_one("#system-info", Static)
        
        # Check if index exists
        index_status = "Loaded" if self.rag_system.index_data else "Not loaded"
        if INDEX_FILE.exists():
            index_size = INDEX_FILE.stat().st_size // 1024  # KB
            index_status = f"Available ({index_size} KB)"
        
        # Active models
        active_models = list(self.model_manager.active_servers.keys())
        active_models_str = ", ".join(active_models) if active_models else "None"
        
        # LM Studio API status
        api_status = "Available" if self.model_manager.lmstudio_client else "Not available"
        
        # Build info table
        table = Table(box=None)
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        
        table.add_row("Current LLM", self.rag_system.llm_model)
        table.add_row("Index Status", index_status)
        table.add_row("Active Models", active_models_str)
        table.add_row("LM Studio API", api_status)
        
        info_widget.update(table)
    
    async def load_index_async(self) -> None:
        """Load index asynchronously"""
        progress_label = self.query_one("#progress-label", Static)
        progress_bar = self.query_one("#progress-bar", Static)
        
        def update_progress(status: str, fraction: float):
            self.call_from_thread(progress_label.update, status)
            
            # Create progress bar
            width = 30
            filled = int(width * fraction)
            bar = f"[{'#' * filled}{'-' * (width - filled)}] {int(fraction * 100)}%"
            self.call_from_thread(progress_bar.update, bar)
        
        # Run in separate thread to avoid blocking UI
        def load_index_thread():
            if not INDEX_FILE.exists():
                update_progress("Building new index...", 0.0)
                success = self.rag_system.build_index(update_progress)
            else:
                update_progress("Loading existing index...", 0.0)
                success = self.rag_system.load_index(update_progress)
            
            # Clear progress after completion
            self.call_from_thread(self.update_system_info)
            time.sleep(2)  # Keep message visible for 2 seconds
            self.call_from_thread(progress_label.update, "")
            self.call_from_thread(progress_bar.update, "")
        
        # Start thread
        threading.Thread(target=load_index_thread, daemon=True).start()
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """When model selection changes"""
        if event.select.id == "model-selector":
            self.rag_system.llm_model = event.value
            self.update_system_info()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "send-btn":
            self.send_query()
        elif button_id == "build-index-btn":
            self.load_index_async()
        elif button_id == "clear-chat-btn":
            self.action_clear_chat()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """When user submits input with Enter key"""
        if event.input.id == "query-input":
            self.send_query()
    
    def send_query(self) -> None:
        """Send query to RAG system"""
        # Get query
        input_widget = self.query_one("#query-input", Input)
        query = input_widget.value.strip()
        
        if not query:
            return
        
        # Clear input
        input_widget.value = ""
        
        # Display query in chat log
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(Panel(f"[bold cyan]You:[/] {query}"))
        
        # Process in separate thread to avoid blocking UI
        def process_query():
            # Display thinking message
            self.call_from_thread(chat_log.write, "[italic]Thinking...[/]")
            
            # Get answer
            result = self.rag_system.ask(query)
            
            # Remove thinking message (last line)
            self.call_from_thread(chat_log.write, "")  # Add empty line
            
            # Display answer
            if result["success"]:
                answer_md = Markdown(result["answer"])
                self.call_from_thread(chat_log.write, Panel(answer_md, title="[bold green]Assistant[/]"))
                
                # Display sources
                if result["sources"]:
                    sources_text = Text.from_markup("[bold blue]Sources:[/]\n")
                    seen_urls = set()
                    
                    for i, source in enumerate(result["sources"], 1):
                        meta = source["metadata"]
                        url = meta.get("url", "")
                        
                        if url in seen_urls:
                            continue
                            
                        seen_urls.add(url)
                        title = meta.get("title", "Untitled")
                        sources_text.append(f"{i}. [bold]{title}[/]\n   {url}\n")
                    
                    self.call_from_thread(chat_log.write, Panel(sources_text, title="[bold blue]References[/]"))
            else:
                self.call_from_thread(chat_log.write, Panel(f"[bold red]Error:[/] {result['answer']}"))
                
            # Update system info
            self.call_from_thread(self.update_system_info)
        
        # Start processing thread
        threading.Thread(target=process_query, daemon=True).start()
    
    def action_clear_chat(self) -> None:
        """Clear chat history"""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.clear()
        self.rag_system.chat_history = []
    
    def action_reload_index(self) -> None:
        """Reload index"""
        self.load_index_async()
    
    def action_change_model(self) -> None:
        """Focus model selector"""
        model_selector = self.query_one("#model-selector", Select)
        model_selector.focus()


# === Main Entry Point ===
def main():
    """Run the LBRXCHAT TUI application"""
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main() 