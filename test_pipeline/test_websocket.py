#!/usr/bin/env python3
import asyncio
import websockets
import json
import base64

async def test_websocket():
    uri = "ws://0.0.0.0:8126/v1/audio/transcriptions"
    
    # Read audio file
    with open("/Users/maciejgad/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/20241109 072723-22BECC3C.m4a", "rb") as f:
        audio_data = f.read()
    
    async with websockets.connect(uri) as websocket:
        # Send audio data
        message = {
            "type": "audio",
            "data": base64.b64encode(audio_data).decode(),
            "format": "m4a",
            "language": "pl"
        }
        await websocket.send(json.dumps(message))
        
        # Wait for response
        response = await websocket.recv()
        result = json.loads(response)
        print(f"Transcription: {result}")

if __name__ == "__main__":
    asyncio.run(test_websocket())