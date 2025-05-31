#!/usr/bin/env python3
"""
Audio recording functionality with real-time processing
"""

import asyncio
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Callable, Any
import numpy as np
import sounddevice as sd
import soundfile as sf
from datetime import datetime


class AudioRecorder:
    """Real-time audio recorder with callback support"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[int] = None,
        chunk_duration: float = 0.5
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recorded_audio = []
        self.stream = None
        
        # Callbacks
        self.on_audio_chunk: Optional[Callable[[np.ndarray], None]] = None
        self.on_level_update: Optional[Callable[[float], None]] = None
        
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Copy audio data
        audio_chunk = indata.copy()
        
        # Add to queue
        self.audio_queue.put(audio_chunk)
        
        # Store for saving
        self.recorded_audio.append(audio_chunk)
        
        # Calculate RMS level
        rms = np.sqrt(np.mean(audio_chunk**2))
        
        # Call callbacks
        if self.on_audio_chunk:
            self.on_audio_chunk(audio_chunk)
        
        if self.on_level_update:
            self.on_level_update(float(rms))
    
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.recorded_audio = []
        
        # Start audio stream
        self.stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self.audio_callback,
            blocksize=self.chunk_size
        )
        
        self.stream.start()
        print(f"Recording started on device {self.device}")
    
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return audio data"""
        if not self.is_recording:
            return np.array([])
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Concatenate all audio chunks
        if self.recorded_audio:
            audio_data = np.concatenate(self.recorded_audio, axis=0)
            return audio_data
        
        return np.array([])
    
    def save_recording(self, audio_data: np.ndarray, filename: str):
        """Save audio data to file"""
        sf.write(filename, audio_data, self.sample_rate)
        print(f"Audio saved to {filename}")
    
    def get_devices(self):
        """Get list of available audio devices"""
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return devices


class VADRecorder(AudioRecorder):
    """Voice Activity Detection recorder"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vad_threshold = 0.01
        self.silence_duration = 2.0  # seconds
        self.min_speech_duration = 0.5  # seconds
        
        self.is_speaking = False
        self.on_speech_end = None  # Initialize callback
        self.silence_start = None
        self.speech_chunks = []
        
    def audio_callback(self, indata, frames, time_info, status):
        """Enhanced callback with VAD"""
        super().audio_callback(indata, frames, time_info, status)
        
        # Simple VAD based on RMS
        rms = np.sqrt(np.mean(indata**2))
        
        if rms > self.vad_threshold:
            # Speech detected
            self.is_speaking = True
            self.silence_start = None
            self.speech_chunks.append(indata.copy())
        else:
            # Silence detected
            if self.is_speaking:
                if self.silence_start is None:
                    self.silence_start = time.time()
                elif time.time() - self.silence_start > self.silence_duration:
                    # End of speech
                    self.is_speaking = False
                    
                    # Check minimum duration
                    speech_duration = len(self.speech_chunks) * self.chunk_duration
                    if speech_duration >= self.min_speech_duration:
                        # Process speech
                        if self.on_speech_end:
                            speech_audio = np.concatenate(self.speech_chunks, axis=0)
                            self.on_speech_end(speech_audio)
                    
                    self.speech_chunks = []
    
    def set_on_speech_end(self, callback: Callable[[np.ndarray], None]):
        """Set callback for when speech ends"""
        self.on_speech_end = callback


class AudioPlayer:
    """Simple audio player"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.is_playing = False
        
    def play(self, audio_data: np.ndarray, blocking: bool = False):
        """Play audio data"""
        try:
            sd.play(audio_data, self.sample_rate)
            if blocking:
                sd.wait()
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def stop(self):
        """Stop playback"""
        sd.stop()


# WebRTC VAD integration (optional, more accurate)
try:
    import webrtcvad
    
    class WebRTCVAD:
        """WebRTC-based Voice Activity Detection"""
        
        def __init__(self, mode: int = 3, sample_rate: int = 16000):
            self.vad = webrtcvad.Vad(mode)  # 0-3, 3 is most aggressive
            self.sample_rate = sample_rate
            self.frame_duration = 30  # ms
            self.frame_size = int(sample_rate * self.frame_duration / 1000)
            
        def is_speech(self, audio_chunk: np.ndarray) -> bool:
            """Check if audio chunk contains speech"""
            # Convert to 16-bit PCM
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            
            # Process in frames
            num_frames = len(audio_int16) // self.frame_size
            speech_frames = 0
            
            for i in range(num_frames):
                frame = audio_int16[i * self.frame_size:(i + 1) * self.frame_size]
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    speech_frames += 1
            
            # Return True if majority of frames contain speech
            return speech_frames > num_frames * 0.5
            
except ImportError:
    WebRTCVAD = None
    print("WebRTC VAD not available. Install with: pip install webrtcvad")


if __name__ == "__main__":
    # Test audio recording
    recorder = AudioRecorder()
    
    print("Available devices:")
    for device in recorder.get_devices():
        print(f"  {device['id']}: {device['name']} ({device['channels']} ch)")
    
    # Record for 5 seconds
    print("\nRecording for 5 seconds...")
    recorder.start_recording()
    time.sleep(5)
    audio = recorder.stop_recording()
    
    # Save recording
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_recording_{timestamp}.wav"
    recorder.save_recording(audio, filename)
    print(f"Saved to {filename}")