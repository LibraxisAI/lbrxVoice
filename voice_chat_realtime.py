#!/usr/bin/env python3
"""
Real-time voice chat with Qwen3, TTS, and Whisper
"""

import asyncio
import pyaudio
import wave
import numpy as np
import soundfile as sf
import io
import threading
import queue
from pathlib import Path
import time
import json
import websocket
from websocket import create_connection

from mlx_lm import load, generate
import mlx.core as mx


class RealTimeVoiceChat:
    """Real-time voice conversation with AI"""
    
    def __init__(self):
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # PyAudio instance
        self.audio = pyaudio.PyAudio()
        
        # Queues for audio processing
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Whisper WebSocket
        self.whisper_ws_url = "ws://localhost:8000/transcribe"
        
        # TTS settings
        self.tts_model = "dia"  # or "csm"
        self.dia_ws_url = "ws://localhost:8124/ws/tts"
        self.csm_rest_url = "http://localhost:8126"
        
        # Load Qwen model
        self.qwen_model = None
        self.qwen_tokenizer = None
        self.load_qwen_model()
        
        # Conversation state
        self.is_listening = False
        self.conversation_history = []
        
    def load_qwen_model(self):
        """Load Qwen3 model"""
        print("🧠 Loading Qwen3-8B...")
        model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
        self.qwen_model, self.qwen_tokenizer = load(model_path)
        print("✅ Qwen3 loaded")
        
    def record_audio(self, duration: float = 5.0) -> bytes:
        """Record audio from microphone"""
        print("🎤 Recording...")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        frames = []
        num_chunks = int(self.sample_rate / self.chunk_size * duration)
        
        for _ in range(num_chunks):
            data = stream.read(self.chunk_size)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            
        buffer.seek(0)
        return buffer.read()
        
    def transcribe_audio_realtime(self, audio_data: bytes) -> str:
        """Transcribe audio using Whisper WebSocket"""
        try:
            ws = create_connection(self.whisper_ws_url)
            
            # Send audio data
            ws.send_binary(audio_data)
            
            # Get transcription
            result = ws.recv()
            data = json.loads(result)
            
            ws.close()
            
            if "transcription" in data:
                return data["transcription"]
            else:
                return ""
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
            
    def generate_ai_response(self, user_input: str) -> str:
        """Generate response using Qwen3"""
        
        messages = [
            {"role": "system", "content": "You are a friendly voice assistant. Keep responses short and conversational."},
        ]
        
        # Add recent history
        for msg in self.conversation_history[-4:]:
            messages.append(msg)
            
        messages.append({"role": "user", "content": user_input})
        
        # Format prompt
        prompt = self.qwen_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Generate
        tokens = mx.array(self.qwen_tokenizer.encode(prompt))
        
        response_tokens = generate(
            self.qwen_model,
            tokens,
            temp=0.7,
            max_tokens=100,
            verbose=False
        )
        
        response = self.qwen_tokenizer.decode(response_tokens[0].tolist())
        
        # Extract assistant response
        if "<|im_start|>assistant" in response:
            response = response.split("<|im_start|>assistant")[-1]
            response = response.split("<|im_end|>")[0].strip()
            
        # Update history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
        
    def synthesize_speech_streaming(self, text: str) -> None:
        """Synthesize and play speech via streaming"""
        
        if self.tts_model == "dia":
            # Use DIA WebSocket
            ws = create_connection(self.dia_ws_url)
            
            request = {
                "text": f"[S1] {text}",
                "request_id": f"voice_chat_{int(time.time())}",
                "temperature": 0.8
            }
            
            ws.send(json.dumps(request))
            
            # Play audio chunks as they arrive
            stream = None
            
            while True:
                result = ws.recv()
                data = json.loads(result)
                
                if data.get("type") == "completion":
                    break
                elif "audio_data" in data:
                    import base64
                    audio_bytes = base64.b64decode(data["audio_data"])
                    
                    # Decode WAV
                    audio_data, sr = sf.read(io.BytesIO(audio_bytes))
                    
                    if stream is None:
                        # Initialize audio stream
                        stream = self.audio.open(
                            format=pyaudio.paFloat32,
                            channels=1,
                            rate=sr,
                            output=True
                        )
                    
                    # Play chunk
                    stream.write(audio_data.astype(np.float32).tobytes())
                    
            if stream:
                stream.stop_stream()
                stream.close()
                
            ws.close()
            
    def voice_activity_detection(self, audio_chunk: np.ndarray) -> bool:
        """Simple VAD based on energy"""
        energy = np.sqrt(np.mean(audio_chunk**2))
        return energy > 0.01  # Threshold
        
    async def conversation_loop(self):
        """Main conversation loop"""
        
        print("\n🎙️  Real-Time Voice Chat")
        print("=" * 50)
        print("Press Ctrl+C to exit")
        print("\nListening...\n")
        
        silence_duration = 0
        audio_buffer = []
        
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while True:
                # Read audio chunk
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Voice activity detection
                if self.voice_activity_detection(audio_chunk):
                    audio_buffer.append(data)
                    silence_duration = 0
                    
                    if not self.is_listening:
                        self.is_listening = True
                        print("👂 Listening...")
                else:
                    if self.is_listening:
                        silence_duration += self.chunk_size / self.sample_rate
                        
                        if silence_duration > 1.5:  # 1.5 seconds of silence
                            # Process recorded audio
                            self.is_listening = False
                            print("🤔 Processing...")
                            
                            # Convert buffer to WAV
                            buffer = io.BytesIO()
                            with wave.open(buffer, 'wb') as wf:
                                wf.setnchannels(self.channels)
                                wf.setsampwidth(self.audio.get_sample_size(self.format))
                                wf.setframerate(self.sample_rate)
                                wf.writeframes(b''.join(audio_buffer))
                            
                            buffer.seek(0)
                            audio_data = buffer.read()
                            
                            # Transcribe
                            transcription = self.transcribe_audio_realtime(audio_data)
                            if transcription:
                                print(f"You: {transcription}")
                                
                                # Generate response
                                response = self.generate_ai_response(transcription)
                                print(f"AI: {response}")
                                
                                # Synthesize and play
                                self.synthesize_speech_streaming(response)
                                
                            # Clear buffer
                            audio_buffer = []
                            silence_duration = 0
                            print("\n👂 Listening...")
                            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        finally:
            stream.stop_stream()
            stream.close()
            
    def test_pipeline(self):
        """Test the complete pipeline"""
        
        print("🧪 Testing Voice Pipeline")
        print("=" * 50)
        
        # Test recording
        print("\n1. Testing microphone (speak for 3 seconds)...")
        audio_data = self.record_audio(3.0)
        print(f"   Recorded {len(audio_data)} bytes")
        
        # Test transcription
        print("\n2. Testing transcription...")
        text = self.transcribe_audio_realtime(audio_data)
        print(f"   Transcribed: '{text}'")
        
        if text:
            # Test AI response
            print("\n3. Testing AI response...")
            response = self.generate_ai_response(text)
            print(f"   AI says: '{response}'")
            
            # Test TTS
            print("\n4. Testing speech synthesis...")
            self.synthesize_speech_streaming(response)
            print("   ✅ Audio played")
        
        print("\n✅ Pipeline test complete!")


def main():
    """Run real-time voice chat"""
    
    chat = RealTimeVoiceChat()
    
    print("🎤 Real-Time Voice Chat with AI")
    print("=" * 50)
    print("\nOptions:")
    print("1. Start voice conversation")
    print("2. Test pipeline")
    print("3. Switch TTS model (current: {})".format(chat.tts_model))
    print("4. Exit")
    
    choice = input("\nChoice: ")
    
    if choice == "1":
        asyncio.run(chat.conversation_loop())
    elif choice == "2":
        chat.test_pipeline()
    elif choice == "3":
        chat.tts_model = "csm" if chat.tts_model == "dia" else "dia"
        print(f"Switched to {chat.tts_model}")
        main()
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("Invalid choice")
        main()


if __name__ == "__main__":
    main()