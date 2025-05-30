#!/usr/bin/env python3
"""
WebSocket client for testing real-time transcription.
"""
import asyncio
import json
import os
import argparse
import base64
import sys
from pathlib import Path

import websockets
import numpy as np


async def send_audio_file(websocket, file_path, chunk_size=4000, interval=0.1):
    """
    Send an audio file to the WebSocket server in chunks.
    
    Args:
        websocket: WebSocket connection
        file_path: Path to the audio file
        chunk_size: Size of each audio chunk in bytes
        interval: Interval between chunks in seconds
    """
    # Read the audio file
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    # Send the audio data in chunks
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        
        # Create a JSON message with base64-encoded audio
        message = {
            "audio": base64.b64encode(chunk).decode("utf-8"),
            "sequence_number": i // chunk_size
        }
        
        # Send the message
        await websocket.send(json.dumps(message))
        
        # Receive and print the response
        response = await websocket.recv()
        result = json.loads(response)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Transcription: {result.get('text', '')}")
            if "segments" in result and result["segments"]:
                for segment in result["segments"]:
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    text = segment.get("text", "")
                    print(f"  [{start:.2f}s - {end:.2f}s] {text}")
        
        # Wait before sending the next chunk
        await asyncio.sleep(interval)


async def capture_and_stream_audio(websocket, device=None, sample_rate=16000, channels=1, duration=None):
    """
    Capture audio from the microphone and stream it to the WebSocket server.
    
    Args:
        websocket: WebSocket connection
        device: Audio device to use
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        duration: Duration in seconds (None for continuous streaming)
    """
    try:
        import sounddevice as sd
        
        # Create a queue for thread-safe communication
        audio_queue = asyncio.Queue(maxsize=20)
        
        # Get the current event loop
        loop = asyncio.get_event_loop()
        
        # Define a non-async callback for sounddevice that puts data in the queue
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            
            # Convert to mono if needed
            if channels > 1:
                indata = np.mean(indata, axis=1)
            
            # Convert to bytes
            audio_bytes = (indata * 32767).astype(np.int16).tobytes()
            
            # Create a JSON message with base64-encoded audio
            message = {
                "audio": base64.b64encode(audio_bytes).decode("utf-8"),
            }
            
            # Schedule putting the message into the queue using the event loop's thread
            # This is thread-safe and avoids the "no running event loop" error
            loop.call_soon_threadsafe(audio_queue.put_nowait, json.dumps(message))
        
        # Coroutine to process audio data from the queue and send to WebSocket
        async def audio_producer():
            while True:
                try:
                    # Get the next message from the queue
                    message = await audio_queue.get()
                    
                    # Send the message
                    await websocket.send(message)
                    
                    # Receive and print the response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        result = json.loads(response)
                        
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        elif result.get("text"):
                            print(f"Transcription: {result.get('text', '')}")
                    except asyncio.TimeoutError:
                        # No response yet, that's fine
                        pass
                    
                    # Mark this task as done
                    audio_queue.task_done()
                except asyncio.CancelledError:
                    # Producer is being cancelled, exit the loop
                    break
                except Exception as e:
                    print(f"Error in audio producer: {e}")
        
        # Set up the audio stream
        block_size = int(sample_rate * 0.5)  # 0.5 seconds per block
        
        # Create an event to signal when to stop
        stop_event = asyncio.Event()
        
        # Start the audio producer task
        producer_task = asyncio.create_task(audio_producer())
        
        # Start the audio input stream
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            callback=audio_callback,
            blocksize=block_size,
            device=device,
        )
        
        stream.start()
        print(f"Streaming audio from microphone (press Ctrl+C to stop)...")
        
        try:
            # If duration is specified, wait that long
            if duration:
                await asyncio.sleep(duration)
                stop_event.set()
            else:
                # Wait until the user presses Ctrl+C
                await stop_event.wait()
        finally:
            # Clean up resources
            stream.stop()
            stream.close()
            producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                pass
                
    except ImportError:
        print("Error: sounddevice module is required for microphone streaming")
        print("Install with: pip install sounddevice")
        sys.exit(1)


async def main():
    """Run the WebSocket client."""
    parser = argparse.ArgumentParser(description="WebSocket client for real-time transcription")
    parser.add_argument("--server", default="ws://localhost:8000/v1/audio/transcriptions", 
                        help="WebSocket server URL (default: ws://localhost:8000/v1/audio/transcriptions)")
    parser.add_argument("--file", help="Audio file to transcribe")
    parser.add_argument("--chunk-size", type=int, default=4000, help="Chunk size in bytes (default: 4000)")
    parser.add_argument("--interval", type=float, default=0.1, help="Interval between chunks in seconds (default: 0.1)")
    parser.add_argument("--microphone", action="store_true", help="Use microphone as input")
    parser.add_argument("--duration", type=float, help="Duration in seconds for microphone streaming")
    parser.add_argument("--list-devices", action="store_true", help="List available audio devices")
    parser.add_argument("--device", type=int, help="Audio device ID to use for microphone capture")
    args = parser.parse_args()
    
    # List audio devices if requested
    if args.list_devices:
        try:
            import sounddevice as sd
            print("Available audio devices:")
            print(sd.query_devices())
        except ImportError:
            print("Error: sounddevice module is required for listing audio devices")
            print("Install with: pip install sounddevice")
        return
    
    # Connect to the WebSocket server
    try:
        async with websockets.connect(args.server) as websocket:
            print(f"Connected to {args.server}")
            
            if args.microphone:
                # Stream audio from microphone
                await capture_and_stream_audio(
                    websocket, 
                    device=args.device, 
                    duration=args.duration
                )
            elif args.file:
                # Send an audio file
                if not os.path.exists(args.file):
                    print(f"Error: File not found: {args.file}")
                    return
                
                await send_audio_file(
                    websocket, 
                    args.file, 
                    chunk_size=args.chunk_size, 
                    interval=args.interval
                )
            else:
                print("Error: No input source specified")
                print("Use --file to specify an audio file or --microphone to use the microphone")
                return
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
