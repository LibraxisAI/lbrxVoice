#!/usr/bin/env python3
"""Test audio recording functionality"""

import asyncio
import sounddevice as sd
import numpy as np
import time

print("🎤 Testing audio recording...")

# List devices
print("\nAvailable audio devices:")
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"  [{i}] {d['name']} ({d['max_input_channels']} ch)")

# Test recording
print("\n📍 Testing 3 second recording...")
duration = 3  # seconds
fs = 16000  # Sample rate

try:
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    print(f"✅ Recorded {len(recording)} samples")
    
    # Check audio level
    max_level = np.max(np.abs(recording))
    print(f"📊 Max level: {max_level:.3f}")
    
    if max_level < 0.001:
        print("⚠️  Warning: Very low audio level detected")
        print("    Make sure microphone permissions are granted")
    else:
        print("✅ Audio level OK")
        
except Exception as e:
    print(f"❌ Recording failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check microphone permissions in System Preferences")
    print("2. Make sure Terminal/iTerm has microphone access")
    print("3. Try selecting a specific device")

print("\n✅ Test complete!")