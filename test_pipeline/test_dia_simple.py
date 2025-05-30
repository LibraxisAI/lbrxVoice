#!/usr/bin/env python3
import requests
import time
import subprocess
import tempfile

# Simple test
text = "Testing DIA text to speech. Can you hear me now?"

url = "http://0.0.0.0:8132/synthesize"
data = {
    "text": text,
    "model": "dia-1.6b",
    "voice": "default",
    "audio_format": "wav"
}

print(f"Generating TTS: {text}")
response = requests.post(url, json=data)

if response.status_code == 202:
    job_id = response.json()['request_id']
    print(f"Job ID: {job_id}")
    
    # Wait for completion
    time.sleep(2)
    
    # Get status
    status_response = requests.get(f"http://0.0.0.0:8132/status/{job_id}")
    if status_response.status_code == 200:
        audio_url = status_response.json()['audio_url']
        
        # Download audio
        audio_response = requests.get(f"http://0.0.0.0:8132{audio_url}")
        
        # Save and play
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_response.content)
            temp_path = tmp.name
        
        print(f"Playing: {temp_path}")
        
        # First check if it's silent
        result = subprocess.run(
            ["ffmpeg", "-i", temp_path, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True
        )
        print("\nVolume analysis:")
        for line in result.stderr.split('\n'):
            if 'volume' in line and 'dB' in line:
                print(line.strip())
        
        # Play with volume boost
        print("\nPlaying with volume boost...")
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-af", "volume=50dB", temp_path])
        
        # Clean up
        import os
        os.unlink(temp_path)
else:
    print(f"Error: {response.status_code}")
    print(response.text)