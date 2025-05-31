#!/usr/bin/env python3
"""
Audio Spectrogram Widget for Textual
Real-time audio visualization using ASCII art
"""

import numpy as np
from typing import Optional, List
from collections import deque
from textual.widget import Widget
from textual.reactive import reactive
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel


class AudioSpectrogram(Widget):
    """ASCII-based audio spectrogram for terminal display"""
    
    # Reactive properties
    audio_level = reactive(0.0)
    is_active = reactive(False)
    
    # ASCII characters for different intensity levels
    CHARS = " ·▁▂▃▄▅▆▇█"
    
    def __init__(self, 
                 history_size: int = 60,
                 **kwargs):
        super().__init__(**kwargs)
        self.history_size = history_size
        
        # Dynamic dimensions based on widget size
        self.spec_width = 60  # Will be updated in get_content_width()
        self.spec_height = 12  # Will be updated in get_content_height()
        
        # History buffer for spectrogram
        self.history = deque(maxlen=history_size)
        
        # Frequency bins - will be updated dynamically
        self.freq_bins = self.spec_height
        self.freq_labels = self._generate_freq_labels()
        
        # Initialize with zeros
        for _ in range(history_size):
            self.history.append(np.zeros(self.freq_bins))
    
    def _generate_freq_labels(self) -> List[str]:
        """Generate frequency labels for display"""
        # Common frequencies in Hz
        freqs = [100, 200, 400, 800, 1600, 3200, 6400, 12800]
        
        # Map to available bins
        labels = []
        for i in range(self.spec_height):
            freq_idx = int(i * len(freqs) / self.spec_height)
            freq = freqs[min(freq_idx, len(freqs)-1)]
            if freq >= 1000:
                labels.append(f"{freq/1000:.1f}k")
            else:
                labels.append(f"{freq}")
        
        return labels[::-1]  # Reverse so high freq is at top
    
    def update_spectrum(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """Update spectrogram with new audio data"""
        if len(audio_data) == 0:
            return
        
        # Simple FFT-based spectrum
        try:
            # Window the data
            window = np.hanning(len(audio_data))
            windowed = audio_data * window
            
            # Compute FFT
            fft = np.fft.rfft(windowed)
            magnitude = np.abs(fft)
            
            # Convert to dB
            magnitude_db = 20 * np.log10(magnitude + 1e-10)
            
            # Bin into frequency bands
            bins = np.linspace(0, len(magnitude_db), self.freq_bins + 1, dtype=int)
            spectrum = np.zeros(self.freq_bins)
            
            for i in range(self.freq_bins):
                if bins[i] < bins[i+1]:
                    spectrum[i] = np.mean(magnitude_db[bins[i]:bins[i+1]])
            
            # Normalize to 0-1
            spectrum = (spectrum - spectrum.min()) / (spectrum.max() - spectrum.min() + 1e-10)
            
            # Add to history
            self.history.append(spectrum)
            
        except Exception:
            # On error, add zeros
            self.history.append(np.zeros(self.freq_bins))
        
        # Update display
        self.refresh()
    
    def update_level(self, level: float):
        """Update simple level meter"""
        self.audio_level = max(0.0, min(1.0, level))
        
        # Create simple spectrum from level
        if self.is_active:
            # Simulate frequency content based on level
            spectrum = np.zeros(self.freq_bins)
            
            # Low frequencies get more energy
            for i in range(self.freq_bins):
                energy = level * (1.0 - i / self.freq_bins) * np.random.uniform(0.5, 1.0)
                spectrum[i] = min(1.0, energy)
            
            self.history.append(spectrum)
            self.refresh()
    
    def render(self) -> RenderableType:
        """Render the spectrogram"""
        # Update dimensions based on current widget size
        self._update_dimensions()
        lines = []
        
        # Title
        status = "🔴 Recording" if self.is_active else "⚪ Idle"
        lines.append(f"[bold]Audio Spectrogram[/bold] {status}")
        lines.append("")
        
        # Spectrogram
        for freq_idx in range(self.freq_bins):
            # Frequency label
            freq_label = self.freq_labels[freq_idx].rjust(5)
            line = f"[dim]{freq_label}Hz[/dim] "
            
            # Spectrum data
            for time_idx in range(len(self.history)):
                value = self.history[time_idx][freq_idx]
                char_idx = int(value * (len(self.CHARS) - 1))
                char = self.CHARS[char_idx]
                
                # Color based on intensity
                if value > 0.8:
                    line += f"[red]{char}[/red]"
                elif value > 0.6:
                    line += f"[yellow]{char}[/yellow]"
                elif value > 0.4:
                    line += f"[green]{char}[/green]"
                elif value > 0.2:
                    line += f"[blue]{char}[/blue]"
                else:
                    line += f"[dim]{char}[/dim]"
            
            lines.append(line)
        
        # Time axis - responsive width
        available_width = max(20, min(self.spec_width, len(self.history)))
        lines.append(" " * 8 + "└" + "─" * available_width)
        lines.append(" " * 8 + " Past " + " " * max(0, (available_width - 10)) + " Now")
        
        # Level meter - responsive width
        level_bar_width = max(20, min(60, self.spec_width - 10))
        level_filled = int(self.audio_level * level_bar_width)
        level_bar = "█" * level_filled + "░" * (level_bar_width - level_filled)
        
        lines.append("")
        lines.append(f"Level: [{level_bar}] {self.audio_level:.1%}")
        
        # Join all lines
        content = Text.from_markup("\n".join(lines))
        
        return Panel(
            content,
            title="🎤 Audio Visualization",
            border_style="green" if self.is_active else "dim"
        )
    
    def start_recording(self):
        """Mark as recording"""
        self.is_active = True
        self.refresh()
    
    def stop_recording(self):
        """Mark as stopped"""
        self.is_active = False
        self.audio_level = 0.0
        self.refresh()
    
    def clear(self):
        """Clear the spectrogram"""
        self.history.clear()
        for _ in range(self.history_size):
            self.history.append(np.zeros(self.freq_bins))
        self.audio_level = 0.0
        self.refresh()
    
    def _update_dimensions(self):
        """Update dimensions based on widget size"""
        # Get available space from widget size
        size = self.size
        if size.width > 0 and size.height > 0:
            # Leave space for labels and borders
            self.spec_width = max(20, size.width - 15)
            self.spec_height = max(6, size.height - 8)
            
            # Update frequency bins if height changed
            if self.freq_bins != self.spec_height:
                self.freq_bins = self.spec_height
                self.freq_labels = self._generate_freq_labels()
                
                # Adjust history buffer for new freq_bins
                new_history = deque(maxlen=self.history_size)
                for _ in range(len(self.history)):
                    new_history.append(np.zeros(self.freq_bins))
                self.history = new_history