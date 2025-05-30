#!/usr/bin/env python3
import requests
import tempfile
import subprocess

# Create test audio with English text
text = "Hello, this is a test of the Whisper transcription service. Testing one two three."

# Generate audio using macOS say command
with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
    tmp_path = tmp.name

# Generate audio
subprocess.run(["say", "-o", tmp_path, text])

# Convert to WAV
wav_path = tmp_path.replace(".aiff", ".wav")
subprocess.run(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path], 
               capture_output=True)

print(f"Generated test audio: {wav_path}")
print(f"Original text: {text}")

# Test transcription
url = "http://0.0.0.0:8123/v1/audio/transcriptions"
with open(wav_path, "rb") as f:
    files = {"file": ("test.wav", f, "audio/wav")}
    data = {"response_format": "json"}
    
    print("\nSending to Whisper...")
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print(f"\nTranscription result:")
    print(f"Text: {result.get('text', '')}")
    print(f"Language: {result.get('language', '')}")
    
    # Compare
    print(f"\nOriginal: {text}")
    print(f"Transcribed: {result.get('text', '')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Clean up
import os
os.unlink(tmp_path)
os.unlink(wav_path)