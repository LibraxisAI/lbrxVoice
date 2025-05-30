#!/usr/bin/env python3
"""
Continue batch transcription for remaining files
"""
import os
import requests
import json
from pathlib import Path
import time

# Directories
UPLOADS_DIR = Path("/Users/maciejgad/LIBRAXIS/Repos/VoiceProcessing/lbrxWhisper/uploads")
OUTPUT_DIR = Path("/Users/maciejgad/LIBRAXIS/Repos/VoiceProcessing/lbrxWhisper/outputs/txt")
API_URL = "http://0.0.0.0:8123/v1/audio/transcriptions"

# Get all audio files without duplicates
audio_files = set()
for ext in ['.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm']:
    for f in UPLOADS_DIR.glob(f"*{ext}"):
        # Skip WAV files that have corresponding M4A files (they're duplicates)
        if f.suffix == '.wav':
            m4a_version = UPLOADS_DIR / f"{f.stem}.m4a"
            if m4a_version.exists():
                continue
        audio_files.add(f)

# Get already transcribed files
transcribed = set(f.stem for f in OUTPUT_DIR.glob("*.txt"))

# Get files to process
to_process = [f for f in audio_files if f.stem not in transcribed]

print(f"Total audio files: {len(audio_files)}")
print(f"Already transcribed: {len(transcribed)}")
print(f"Remaining to process: {len(to_process)}")

if to_process:
    print(f"\nProcessing remaining {len(to_process)} files...")
    
    for i, audio_file in enumerate(to_process, 1):
        print(f"\n[{i}/{len(to_process)}] {audio_file.name}")
        output_file = OUTPUT_DIR / f"{audio_file.stem}.txt"
        
        with open(audio_file, 'rb') as f:
            files = {'file': (audio_file.name, f, 'audio/*')}
            data = {'response_format': 'json'}
            
            try:
                response = requests.post(API_URL, files=files, data=data, timeout=300)
                if response.status_code == 200:
                    result = response.json()
                    text = result.get('text', '')
                    language = result.get('language', 'unknown')
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f"File: {audio_file.name}\n")
                        f.write(f"Language: {language}\n")
                        f.write(f"Transcription:\n")
                        f.write("-" * 40 + "\n")
                        f.write(text)
                    
                    print(f"  ✓ Transcribed ({language})")
                else:
                    print(f"  ✗ Error: {response.status_code}")
            except Exception as e:
                print(f"  ✗ Exception: {str(e)}")
else:
    print("\nAll files have been transcribed!")