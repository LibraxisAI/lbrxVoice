#!/usr/bin/env python3
import requests
import json
import time

# Test DIA TTS
url = "http://0.0.0.0:8132/synthesize"

data = {
    "text": "Welcome to our unique recruitment platform! We are searching for exceptional AI Engineers and ML experts who can bridge the gap between theoretical concepts and practical implementations.",
    "model": "dia-1.6b",
    "voice": "default", 
    "audio_format": "wav"
}

print("Sending TTS request...")
response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print(f"Success! Job ID: {result.get('request_id')}")
    print(f"Audio URL: {result.get('audio_url')}")
    
    # Download audio file
    if result.get('audio_url'):
        audio_url = f"http://0.0.0.0:8132{result['audio_url']}"
        print(f"\nDownloading audio from: {audio_url}")
        
        audio_response = requests.get(audio_url)
        if audio_response.status_code == 200:
            with open("output/dia_test.wav", "wb") as f:
                f.write(audio_response.content)
            print("Audio saved to output/dia_test.wav")
        else:
            print(f"Failed to download audio: {audio_response.status_code}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)