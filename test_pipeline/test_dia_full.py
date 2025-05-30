#!/usr/bin/env python3
import requests
import json
import time

# Full recruitment text
text = """Welcome to our unique recruitment platform! We're searching for exceptional AI Engineers and ML experts who can bridge the gap between theoretical concepts and practical implementations. Whether you're crafting neural architectures in Silicon Valley or optimizing quantum algorithms in Bangalore, we want you on our team!"""

url = "http://0.0.0.0:8132/synthesize"

data = {
    "text": text,
    "model": "dia-1.6b",
    "voice": "default", 
    "audio_format": "wav"
}

print("Sending TTS request for full text...")
response = requests.post(url, json=data)

if response.status_code == 202:
    result = response.json()
    job_id = result.get('request_id')
    print(f"Job submitted: {job_id}")
    
    # Wait for completion
    print("Waiting for generation...")
    time.sleep(2)
    
    # Check status
    status_url = f"http://0.0.0.0:8132/status/{job_id}"
    status_response = requests.get(status_url)
    
    if status_response.status_code == 200:
        status = status_response.json()
        audio_url = status.get('audio_url')
        
        if audio_url:
            # Download audio
            full_url = f"http://0.0.0.0:8132{audio_url}"
            print(f"Downloading from: {full_url}")
            
            audio_response = requests.get(full_url)
            if audio_response.status_code == 200:
                with open("output/dia_recruitment_full.wav", "wb") as f:
                    f.write(audio_response.content)
                print(f"✅ Audio saved to output/dia_recruitment_full.wav")
                print(f"Duration: {status.get('duration'):.2f} seconds")
                print(f"Processing time: {status.get('processing_time'):.2f} seconds")
            else:
                print(f"Failed to download audio: {audio_response.status_code}")
        else:
            print("No audio URL in status response")
    else:
        print(f"Status check failed: {status_response.status_code}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)