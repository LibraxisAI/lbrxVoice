#!/usr/bin/env python3
"""
Transcribe all audio files with forced Polish language setting
"""
import os
import requests
import json
from pathlib import Path
import time

# Directories
UPLOADS_DIR = Path("/Users/maciejgad/LIBRAXIS/Repos/VoiceProcessing/lbrxWhisper/uploads")
OUTPUT_DIR = Path("/Users/maciejgad/LIBRAXIS/Repos/VoiceProcessing/lbrxWhisper/outputs/txt_pl")
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

print(f"Found {len(audio_files)} audio files to transcribe with Polish language setting")
print("=" * 60)

# Process each file
successful = 0
failed = 0

for i, audio_file in enumerate(sorted(audio_files), 1):
    print(f"\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")
    
    output_file = OUTPUT_DIR / f"{audio_file.stem}.txt"
    
    # Transcribe with Polish language forced
    print(f"  → Transcribing with language=pl...")
    start_time = time.time()
    
    with open(audio_file, 'rb') as f:
        files = {'file': (audio_file.name, f, 'audio/*')}
        data = {
            'response_format': 'json',  # API doesn't support 'text' yet
            'language': 'pl',  # Force Polish
            'prompt': 'Transkrybuj dokładnie po polsku.',  # Polish prompt
            'temperature': 0.0  # Lower temperature for more accurate transcription
        }
        
        try:
            response = requests.post(API_URL, files=files, data=data, timeout=300)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '')
                
                # Save as plain text
                with open(output_file, 'w', encoding='utf-8') as out:
                    out.write(text)
                
                print(f"  ✓ Success! Time: {elapsed:.1f}s")
                print(f"  → Saved to: {output_file.name}")
                
                # Show preview
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"  → Preview: {preview}")
                
                successful += 1
            else:
                print(f"  ✗ Failed: HTTP {response.status_code}")
                print(f"  → Error: {response.text}")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
            failed += 1

# Summary
print("\n" + "=" * 60)
print(f"SUMMARY:")
print(f"  Total files: {len(audio_files)}")
print(f"  Successful: {successful}")
print(f"  Failed: {failed}")
print(f"\nOutput directory: {OUTPUT_DIR}")
print("\nNote: All files were transcribed with forced Polish language setting (language='pl')")

# Run directly