#!/usr/bin/env python3
import asyncio
import websockets
import json
import base64
import subprocess
import tempfile

async def test_dia_ws():
    # Check available DIA WebSocket endpoints
    print("Checking DIA WebSocket server...")
    
    # Try to find WebSocket endpoint
    try:
        # Check if DIA has WebSocket server running
        response = subprocess.run(["curl", "-s", "http://0.0.0.0:8132/docs"], 
                                capture_output=True, text=True)
        if "websocket" in response.stdout.lower():
            print("Found WebSocket endpoints in DIA API")
        else:
            print("No WebSocket endpoints found. Using REST API instead.")
            return await test_dia_rest()
    except:
        pass
    
    # If WebSocket not available, fall back to REST
    return await test_dia_rest()

async def test_dia_rest():
    """Use REST API to generate TTS and play"""
    import requests
    
    text = "Hello! This is a test of the DIA text-to-speech system. Let's see if we can hear anything."
    
    # Submit TTS job
    url = "http://0.0.0.0:8132/synthesize"
    data = {
        "text": text,
        "model": "dia-1.6b",
        "voice": "default",
        "audio_format": "wav"
    }
    
    print(f"Sending TTS request: {text[:50]}...")
    response = requests.post(url, json=data)
    
    if response.status_code == 202:
        result = response.json()
        job_id = result.get('request_id')
        print(f"Job submitted: {job_id}")
        
        # Wait and check status
        await asyncio.sleep(2)
        
        status_url = f"http://0.0.0.0:8132/status/{job_id}"
        status_response = requests.get(status_url)
        
        if status_response.status_code == 200:
            status = status_response.json()
            audio_url = status.get('audio_url')
            
            if audio_url:
                # Download audio
                full_url = f"http://0.0.0.0:8132{audio_url}"
                audio_response = requests.get(full_url)
                
                if audio_response.status_code == 200:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(audio_response.content)
                        temp_path = tmp.name
                    
                    print(f"Audio saved to: {temp_path}")
                    
                    # Check volume
                    print("\nChecking audio volume...")
                    vol_check = subprocess.run([
                        "ffmpeg", "-i", temp_path, "-af", "volumedetect", "-f", "null", "-"
                    ], capture_output=True, text=True, stderr=subprocess.STDOUT)
                    
                    for line in vol_check.stdout.split('\n'):
                        if 'mean_volume' in line or 'max_volume' in line:
                            print(line.strip())
                    
                    # Try to normalize and play
                    print("\nNormalizing audio and playing...")
                    normalized_path = temp_path.replace('.wav', '_normalized.wav')
                    
                    # Normalize to -3dB peak
                    subprocess.run([
                        "ffmpeg", "-y", "-i", temp_path,
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        normalized_path
                    ], capture_output=True)
                    
                    # Play normalized audio
                    print("Playing audio...")
                    subprocess.run(["afplay", normalized_path])
                    
                    # Clean up
                    import os
                    os.unlink(temp_path)
                    os.unlink(normalized_path)
                    
                else:
                    print(f"Failed to download audio: {audio_response.status_code}")
        else:
            print(f"Status check failed: {status_response.status_code}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_dia_ws())