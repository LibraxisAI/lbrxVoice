#!/usr/bin/env python3
"""
Test full TTS -> Whisper pipeline
"""

import asyncio
import base64
import json
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import requests
import websocket
from websocket import create_connection


class TTSPipelineTester:
    """Test TTS services and integration with Whisper"""
    
    def __init__(self):
        self.dia_ws_url = "ws://localhost:8124/ws/tts"
        self.dia_rest_url = "http://localhost:8125"
        self.csm_rest_url = "http://localhost:8126"
        self.whisper_batch_url = "http://localhost:8123"
        self.whisper_realtime_url = "ws://localhost:8000/transcribe"
        
        self.test_texts = [
            "[S1] Hello from DIA text to speech model. [S2] This is amazing technology!",
            "[S1] Testing the pipeline integration. (laughs) [S2] Everything seems to work perfectly.",
            "This is CSM model speaking. How does it sound?",
            "Testing different speakers and emotions in the text to speech pipeline."
        ]
        
    def test_dia_websocket(self, text: str) -> bytes:
        """Test DIA WebSocket endpoint"""
        print("\n🔊 Testing DIA WebSocket...")
        
        ws = create_connection(self.dia_ws_url)
        
        # Send TTS request
        request = {
            "text": text,
            "request_id": "test_dia_ws_001",
            "temperature": 0.8,
            "top_p": 0.95
        }
        
        ws.send(json.dumps(request))
        print(f"Sent: {text[:50]}...")
        
        # Collect audio chunks
        audio_chunks = []
        
        while True:
            result = ws.recv()
            data = json.loads(result)
            
            if data.get("type") == "completion":
                print(f"✅ Completed in {data['processing_time']:.2f}s")
                break
            elif "error" in data:
                print(f"❌ Error: {data['error']}")
                break
            elif "audio_data" in data:
                # Decode base64 audio chunk
                audio_data = base64.b64decode(data["audio_data"])
                audio_chunks.append(audio_data)
                print(f"  Received chunk {data['chunk_index']}")
        
        ws.close()
        
        # Combine chunks
        if audio_chunks:
            return b''.join(audio_chunks)
        return b''
        
    def test_dia_rest(self, text: str) -> bytes:
        """Test DIA REST API endpoint"""
        print("\n🔊 Testing DIA REST API...")
        
        # Send synchronous request
        response = requests.post(
            f"{self.dia_rest_url}/synthesize_sync",
            json={
                "text": text,
                "request_id": "test_dia_rest_001",
                "temperature": 0.8,
                "top_p": 0.95
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated in {data['processing_time']:.2f}s")
            
            # Decode base64 audio
            audio_data = base64.b64decode(data["audio_data"])
            return audio_data
        else:
            print(f"❌ Error: {response.text}")
            return b''
            
    def test_csm_rest(self, text: str, speaker_id: int = 0) -> bytes:
        """Test CSM REST API endpoint"""
        print(f"\n🔊 Testing CSM REST API (speaker {speaker_id})...")
        
        # Send synchronous request
        response = requests.post(
            f"{self.csm_rest_url}/synthesize_sync",
            json={
                "text": text,
                "request_id": "test_csm_rest_001",
                "speaker_id": str(speaker_id),
                "temperature": 0.8
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated in {data['processing_time']:.2f}s")
            
            # Decode base64 audio
            audio_data = base64.b64decode(data["audio_data"])
            return audio_data
        else:
            print(f"❌ Error: {response.text}")
            return b''
            
    def test_whisper_batch(self, audio_data: bytes, filename: str) -> str:
        """Test Whisper batch transcription"""
        print("\n📝 Testing Whisper batch transcription...")
        
        # Save audio to file
        temp_path = Path(f"./test_outputs/{filename}")
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(audio_data)
            
        # Upload to Whisper
        with open(temp_path, "rb") as f:
            files = {"file": (filename, f, "audio/wav")}
            data = {"language": "en"}
            
            response = requests.post(
                f"{self.whisper_batch_url}/transcribe",
                files=files,
                data=data
            )
            
        if response.status_code in [200, 202]:
            result = response.json()
            
            if "job_id" in result:
                # Poll for completion
                job_id = result["job_id"]
                print(f"  Job ID: {job_id}")
                
                while True:
                    status_response = requests.get(
                        f"{self.whisper_batch_url}/status/{job_id}"
                    )
                    status = status_response.json()
                    
                    if status["status"] == "completed":
                        print(f"✅ Transcribed: {status['transcription']}")
                        return status["transcription"]
                    elif status["status"] == "failed":
                        print(f"❌ Failed: {status.get('error', 'Unknown error')}")
                        return ""
                    
                    time.sleep(1)
            else:
                print(f"✅ Transcribed: {result.get('transcription', '')}")
                return result.get("transcription", "")
        else:
            print(f"❌ Error: {response.text}")
            return ""
            
    def run_full_pipeline(self):
        """Run complete TTS -> Whisper pipeline test"""
        print("🚀 Starting Full Pipeline Test")
        print("=" * 50)
        
        results = []
        
        # Test 1: DIA WebSocket
        try:
            print("\n[Test 1] DIA WebSocket -> Whisper")
            audio = self.test_dia_websocket(self.test_texts[0])
            if audio:
                transcription = self.test_whisper_batch(audio, "dia_ws_test.wav")
                results.append({
                    "test": "DIA WebSocket",
                    "input": self.test_texts[0],
                    "output": transcription,
                    "success": bool(transcription)
                })
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({"test": "DIA WebSocket", "success": False, "error": str(e)})
            
        # Test 2: DIA REST
        try:
            print("\n[Test 2] DIA REST -> Whisper")
            audio = self.test_dia_rest(self.test_texts[1])
            if audio:
                transcription = self.test_whisper_batch(audio, "dia_rest_test.wav")
                results.append({
                    "test": "DIA REST",
                    "input": self.test_texts[1],
                    "output": transcription,
                    "success": bool(transcription)
                })
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({"test": "DIA REST", "success": False, "error": str(e)})
            
        # Test 3: CSM REST (multiple speakers)
        for speaker_id in [0, 1, 2]:
            try:
                print(f"\n[Test 3.{speaker_id}] CSM REST (Speaker {speaker_id}) -> Whisper")
                audio = self.test_csm_rest(self.test_texts[2], speaker_id)
                if audio:
                    transcription = self.test_whisper_batch(audio, f"csm_speaker{speaker_id}_test.wav")
                    results.append({
                        "test": f"CSM REST (Speaker {speaker_id})",
                        "input": self.test_texts[2],
                        "output": transcription,
                        "success": bool(transcription)
                    })
            except Exception as e:
                print(f"❌ Test failed: {e}")
                results.append({
                    "test": f"CSM REST (Speaker {speaker_id})", 
                    "success": False, 
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        for result in results:
            status = "✅" if result.get("success") else "❌"
            print(f"{status} {result['test']}")
            if result.get("success"):
                print(f"   Input:  {result['input'][:60]}...")
                print(f"   Output: {result['output'][:60]}...")
            else:
                print(f"   Error: {result.get('error', 'Unknown')}")
                
        # Save results
        with open("./test_outputs/pipeline_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"\nResults saved to: ./test_outputs/pipeline_test_results.json")
        
        # Calculate success rate
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n🎯 Success Rate: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        return results


def main():
    """Run pipeline tests"""
    tester = TTSPipelineTester()
    
    # Check if services are running
    print("🔍 Checking services...")
    
    services = [
        ("DIA WebSocket", "http://localhost:8124/health"),
        ("DIA REST", "http://localhost:8125/health"),
        ("CSM REST", "http://localhost:8126/health"),
        ("Whisper Batch", "http://localhost:8123/health"),
    ]
    
    all_healthy = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {name}: Healthy")
            else:
                print(f"❌ {name}: Unhealthy")
                all_healthy = False
        except:
            print(f"❌ {name}: Not running")
            all_healthy = False
            
    if not all_healthy:
        print("\n⚠️  Some services are not running. Start them first:")
        print("  - DIA WebSocket: python -m tts_servers dia-ws")
        print("  - DIA REST: python -m tts_servers dia-rest")
        print("  - CSM REST: python -m tts_servers csm-rest")
        print("  - Whisper Batch: python -m whisper_servers batch")
        return
        
    # Run tests
    print("\n" + "=" * 50)
    results = tester.run_full_pipeline()


if __name__ == "__main__":
    main()