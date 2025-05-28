#!/usr/bin/env python3
"""
Test client for the MLX Whisper batch transcription server.
"""
import sys
import argparse
import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Test client for MLX Whisper batch transcription server")
    parser.add_argument("file", help="Path to audio file to transcribe")
    parser.add_argument("--server", default="http://localhost:8123", help="Server URL (default: http://localhost:8123)")
    parser.add_argument("--model", default="whisper-large-v3", help="Model to use (default: whisper-large-v3)")
    parser.add_argument("--language", help="Language code (optional)")
    parser.add_argument("--prompt", help="Prompt for the model (optional)")
    parser.add_argument("--word-timestamps", action="store_true", help="Include word-level timestamps")
    return parser.parse_args()


def main():
    args = parse_args()
    
    print(f"Sending file {args.file} to server {args.server}")
    
    # Prepare the request
    url = f"{args.server}/v1/audio/transcriptions"
    
    # Prepare form data
    files = {"file": open(args.file, "rb")}
    data = {"model": args.model}
    
    if args.language:
        data["language"] = args.language
    
    if args.prompt:
        data["prompt"] = args.prompt
    
    if args.word_timestamps:
        data["word_timestamps"] = "true"
    
    # Send the request
    try:
        response = requests.post(url, files=files, data=data)
        
        # Check for errors
        response.raise_for_status()
        
        # Print the result
        result = response.json()
        
        print("\nTranscription:")
        print("-" * 50)
        print(result["text"])
        print("-" * 50)
        
        if "segments" in result and result["segments"]:
            print("\nSegments:")
            for i, segment in enumerate(result["segments"]):
                print(f"[{segment.get('start', 0):.2f}s - {segment.get('end', 0):.2f}s] {segment.get('text', '')}")
        
        print(f"\nDetected language: {result.get('language', 'unknown')}")
        print(f"Duration: {result.get('duration', 0):.2f} seconds")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
