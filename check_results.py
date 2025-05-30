#!/usr/bin/env python3
"""
Check transcription results stored on the server
"""
import json
import os
from pathlib import Path

results_dir = Path("results")
print(f"📁 Checking results in: {results_dir.absolute()}\n")

if not results_dir.exists():
    print("❌ Results directory not found!")
    exit(1)

json_files = list(results_dir.glob("*.json"))

if not json_files:
    print("❌ No transcription results found!")
    exit(0)

print(f"✅ Found {len(json_files)} transcription(s):\n")

for i, json_file in enumerate(sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True), 1):
    print(f"{i}. {json_file.name}")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract info
        text = data.get('text', '').strip()
        language = data.get('language', 'unknown')
        duration = data.get('duration', 0)
        
        # File info
        size_kb = json_file.stat().st_size / 1024
        mod_time = json_file.stat().st_mtime
        from datetime import datetime
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"   📅 Created: {mod_date}")
        print(f"   🌐 Language: {language}")
        print(f"   ⏱️  Duration: {duration:.1f}s")
        print(f"   📏 Size: {size_kb:.1f} KB")
        print(f"   📝 Text preview: {text[:100]}{'...' if len(text) > 100 else ''}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        print()

print("\n💡 Tip: Results are saved with job ID as filename (UUID format)")
print("   Each JSON file contains full transcription with segments and timestamps")