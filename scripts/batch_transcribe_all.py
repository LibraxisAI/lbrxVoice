#!/usr/bin/env python3
"""
Batch transcribe all audio files from uploads directory
and save results as txt files with same names in outputs/txt
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

# Supported audio formats
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm', '.aac', '.flac', '.ogg'}

def transcribe_file(file_path: Path) -> dict:
    """Transcribe a single audio file"""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'audio/*')}
        data = {
            'response_format': 'json',
            'language': None  # Auto-detect language
        }
        
        try:
            response = requests.post(API_URL, files=files, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {'error': str(e)}

def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all audio files
    audio_files = []
    for ext in AUDIO_EXTENSIONS:
        audio_files.extend(UPLOADS_DIR.glob(f"*{ext}"))
    
    if not audio_files:
        print("No audio files found in uploads directory")
        return
    
    print(f"Found {len(audio_files)} audio files to transcribe")
    print("=" * 60)
    
    # Process each file
    successful = 0
    failed = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")
        
        # Skip if already transcribed
        output_file = OUTPUT_DIR / f"{audio_file.stem}.txt"
        if output_file.exists():
            print(f"  → Already transcribed, skipping")
            continue
        
        # Transcribe
        print(f"  → Transcribing...")
        start_time = time.time()
        result = transcribe_file(audio_file)
        elapsed = time.time() - start_time
        
        if 'error' in result:
            print(f"  ✗ Failed: {result['error']}")
            failed += 1
        else:
            # Save transcription
            text = result.get('text', '')
            language = result.get('language', 'unknown')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"File: {audio_file.name}\n")
                f.write(f"Language: {language}\n")
                f.write(f"Transcription:\n")
                f.write("-" * 40 + "\n")
                f.write(text)
            
            print(f"  ✓ Success! Language: {language}, Time: {elapsed:.1f}s")
            print(f"  → Saved to: {output_file.name}")
            successful += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Total files: {len(audio_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {len(audio_files) - successful - failed}")
    print(f"\nOutput directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()