#!/usr/bin/env python3
import requests

# File path
file_path = "/Users/maciejgad/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/20241112 003217-AA6AC0B2.m4a"

# API endpoint
url = "http://0.0.0.0:8123/v1/audio/transcriptions"

# Open and send the file
with open(file_path, "rb") as f:
    files = {"file": ("recording.m4a", f, "audio/m4a")}
    data = {
        "language": "pl",
        "response_format": "json"
    }
    
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print("=== TRANSKRYPCJA ===")
    print(result.get("text", ""))
else:
    print(f"Error: {response.status_code}")
    print(response.text)