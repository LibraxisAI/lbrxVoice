#!/usr/bin/env python3
"""
Test TTS -> Whisper pipeline with correct ports
"""

import requests
import json
import base64
import time
from pathlib import Path
import soundfile as sf

def test_csm_to_whisper():
    """Test CSM TTS -> Whisper pipeline"""
    
    print("🎤 Testing CSM -> Whisper pipeline")
    
    # Test text
    text = "Hello from CSM text to speech model. This is a test of the complete pipeline."
    
    # 1. Generate speech with CSM
    print(f"\n1. Generating speech: {text}")
    
    tts_response = requests.post(
        "http://localhost:8135/synthesize_sync",
        json={
            "text": text,
            "speaker_id": "0",
            "request_id": "test_csm_001"
        }
    )
    
    if tts_response.status_code != 200:
        print(f"❌ TTS failed: {tts_response.text}")
        return
        
    tts_data = tts_response.json()
    audio_base64 = tts_data["audio_data"]
    audio_bytes = base64.b64decode(audio_base64)
    
    # Save audio
    audio_path = Path("test_outputs/csm_test.wav")
    audio_path.parent.mkdir(exist_ok=True)
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    
    print(f"✅ Audio saved to: {audio_path}")
    print(f"   Duration: {tts_data['duration']:.2f}s")
    
    # 2. Transcribe with Whisper
    print("\n2. Transcribing with Whisper...")
    
    with open(audio_path, "rb") as f:
        files = {"file": ("test.wav", f, "audio/wav")}
        data = {"language": "en"}
        
        whisper_response = requests.post(
            "http://localhost:8123/transcribe",
            files=files,
            data=data
        )
    
    if whisper_response.status_code not in [200, 202]:
        print(f"❌ Whisper failed: {whisper_response.text}")
        return
        
    result = whisper_response.json()
    
    # Handle async job
    if "job_id" in result:
        job_id = result["job_id"]
        print(f"   Job ID: {job_id}")
        
        # Poll for completion
        while True:
            status_response = requests.get(f"http://localhost:8123/status/{job_id}")
            status = status_response.json()
            
            if status["status"] == "completed":
                transcription = status["transcription"]
                break
            elif status["status"] == "failed":
                print(f"❌ Transcription failed: {status.get('error')}")
                return
            
            time.sleep(1)
    else:
        transcription = result.get("transcription", "")
    
    # 3. Compare results
    print(f"\n✅ Pipeline complete!")
    print(f"   Original:     {text}")
    print(f"   Transcribed:  {transcription}")
    
    # Calculate similarity
    import difflib
    similarity = difflib.SequenceMatcher(None, text.lower(), transcription.lower()).ratio()
    print(f"   Similarity:   {similarity*100:.1f}%")
    
    return {
        "original": text,
        "transcribed": transcription,
        "similarity": similarity,
        "audio_path": str(audio_path)
    }


def check_services():
    """Check if all services are running"""
    services = {
        "Whisper Batch": "http://localhost:8123/health",
        "CSM REST": "http://localhost:8135/health"
    }
    
    print("🔍 Checking services...")
    all_ok = True
    
    for name, url in services.items():
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"✅ {name}: Online")
            else:
                print(f"❌ {name}: Error")
                all_ok = False
        except:
            print(f"❌ {name}: Offline")
            all_ok = False
    
    return all_ok


def main():
    # Check services
    if not check_services():
        print("\n⚠️  Some services are not running!")
        print("Run: python start_servers.py")
        return
    
    print("\n" + "="*50)
    
    # Run test
    result = test_csm_to_whisper()
    
    # Save result
    if result:
        result_path = Path("test_outputs/pipeline_result.json")
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Results saved to: {result_path}")


if __name__ == "__main__":
    main()