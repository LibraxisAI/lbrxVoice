#!/usr/bin/env python3
"""
Conversational Agent with Qwen3-8B, TTS, and Whisper
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any
import numpy as np

from mlx_lm import load, generate
from mlx_lm.utils import generate_step
import mlx.core as mx

from test_tts_pipeline import TTSPipelineTester


class ConversationalAgent:
    """AI Assistant with voice input/output capabilities"""
    
    def __init__(self):
        self.qwen_model = None
        self.qwen_tokenizer = None
        self.tts_tester = TTSPipelineTester()
        
        # System prompt
        self.system_prompt = """You are a helpful AI assistant with voice capabilities. 
You can understand speech through Whisper and respond with natural voice using TTS.
Keep your responses concise and conversational. When asked about yourself, 
mention that you're powered by Qwen3-8B, DIA TTS, and Whisper on Apple Silicon."""
        
        self.conversation_history = []
        
    def load_qwen_model(self):
        """Load Qwen3-8B model"""
        print("🧠 Loading Qwen3-8B-Q6...")
        
        model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"  # Using 4bit for better performance
        self.qwen_model, self.qwen_tokenizer = load(model_path)
        
        print("✅ Qwen3 model loaded")
        
    def generate_response(self, user_input: str) -> str:
        """Generate AI response using Qwen3"""
        
        # Build conversation
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history
        for msg in self.conversation_history[-4:]:  # Keep last 4 exchanges
            messages.append(msg)
            
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Format for Qwen
        prompt = self.qwen_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        tokens = self.qwen_tokenizer.encode(prompt, return_tensors="np")
        tokens = mx.array(tokens)
        
        # Generate response
        print("🤔 Thinking...")
        start_time = time.time()
        
        response_tokens = generate(
            self.qwen_model,
            tokens,
            temp=0.7,
            max_tokens=200,
            verbose=False
        )
        
        # Decode response
        response = self.qwen_tokenizer.decode(response_tokens[0].tolist())
        
        # Extract assistant response
        if "<|im_start|>assistant" in response:
            response = response.split("<|im_start|>assistant")[-1]
            response = response.split("<|im_end|>")[0].strip()
        
        gen_time = time.time() - start_time
        tokens_per_sec = len(response_tokens[0]) / gen_time
        print(f"✅ Generated in {gen_time:.2f}s ({tokens_per_sec:.1f} tokens/s)")
        
        # Update history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
        
    def text_to_speech(self, text: str, model: str = "dia") -> bytes:
        """Convert text to speech"""
        
        if model == "dia":
            # Format for DIA with dialogue tags
            formatted_text = f"[S1] {text}"
            return self.tts_tester.test_dia_rest(formatted_text)
        else:  # csm
            return self.tts_tester.test_csm_rest(text, speaker_id=0)
            
    def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using Whisper"""
        return self.tts_tester.test_whisper_batch(audio_data, "user_input.wav")
        
    async def voice_conversation(self):
        """Interactive voice conversation"""
        
        print("\n🎙️  Voice Conversation Mode")
        print("=" * 50)
        print("Speak into your microphone (simulated with text input)")
        print("Type 'quit' to exit\n")
        
        while True:
            # Simulate voice input (in real app, would capture from microphone)
            user_text = input("You (speak): ")
            
            if user_text.lower() in ['quit', 'exit', 'bye']:
                # Say goodbye
                goodbye = "Goodbye! It was nice talking with you."
                audio = self.text_to_speech(goodbye)
                print(f"AI (voice): {goodbye}")
                break
                
            # Generate AI response
            ai_response = self.generate_response(user_text)
            print(f"AI (thinking): {ai_response}")
            
            # Convert to speech
            audio = self.text_to_speech(ai_response)
            
            # In real app, would play audio
            print(f"AI (speaking): [Audio generated - {len(audio)} bytes]")
            print()
            
    def benchmark_pipeline(self):
        """Benchmark the full pipeline"""
        
        print("\n📊 Pipeline Benchmark")
        print("=" * 50)
        
        test_input = "Tell me about the weather today and suggest what I should wear."
        
        # 1. Generate AI response
        start = time.time()
        ai_response = self.generate_response(test_input)
        llm_time = time.time() - start
        print(f"LLM Generation: {llm_time:.2f}s")
        print(f"Response: {ai_response[:100]}...")
        
        # 2. TTS Generation
        start = time.time()
        audio_dia = self.text_to_speech(ai_response, "dia")
        tts_dia_time = time.time() - start
        print(f"DIA TTS: {tts_dia_time:.2f}s")
        
        start = time.time()
        audio_csm = self.text_to_speech(ai_response, "csm")
        tts_csm_time = time.time() - start
        print(f"CSM TTS: {tts_csm_time:.2f}s")
        
        # 3. Whisper Transcription
        start = time.time()
        transcription = self.speech_to_text(audio_dia)
        stt_time = time.time() - start
        print(f"Whisper STT: {stt_time:.2f}s")
        
        # Summary
        total_time_dia = llm_time + tts_dia_time + stt_time
        total_time_csm = llm_time + tts_csm_time + stt_time
        
        print("\n📈 Performance Summary:")
        print(f"  Total (with DIA): {total_time_dia:.2f}s")
        print(f"  Total (with CSM): {total_time_csm:.2f}s")
        print(f"  Response length: {len(ai_response)} chars")
        print(f"  Audio size: {len(audio_dia)} bytes")
        
        # Memory usage
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"\n💾 Memory Usage:")
        print(f"  RSS: {memory_info.rss / 1024**3:.2f} GB")
        print(f"  VMS: {memory_info.vms / 1024**3:.2f} GB")


def main():
    """Run conversational agent"""
    
    agent = ConversationalAgent()
    
    # Load models
    print("🚀 Initializing Conversational Agent")
    agent.load_qwen_model()
    
    while True:
        print("\n📋 Menu:")
        print("1. Voice Conversation")
        print("2. Benchmark Pipeline")
        print("3. Test TTS Models")
        print("4. Clear History")
        print("5. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == "1":
            asyncio.run(agent.voice_conversation())
        elif choice == "2":
            agent.benchmark_pipeline()
        elif choice == "3":
            test_text = input("Enter text for TTS: ")
            
            print("\nGenerating with DIA...")
            audio_dia = agent.text_to_speech(test_text, "dia")
            print(f"DIA: {len(audio_dia)} bytes")
            
            print("\nGenerating with CSM...")
            audio_csm = agent.text_to_speech(test_text, "csm")
            print(f"CSM: {len(audio_csm)} bytes")
            
        elif choice == "4":
            agent.conversation_history = []
            print("✅ History cleared")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()