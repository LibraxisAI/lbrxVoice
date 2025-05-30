# Testing Guide for lbrxWhisper

## 🎯 Quick Test

### 1. Check if servers are running
```bash
curl http://0.0.0.0:8123/docs  # Should show Swagger UI
```

### 2. Test transcription
```bash
# Upload audio file
curl -X POST "http://0.0.0.0:8123/v1/audio/transcriptions" \
  -F "file=@your_audio.mp3" \
  -F "response_format=json"
```

## 📁 Where are results stored?

All transcriptions are saved in the `results/` directory on the server:
- Location: `lbrxWhisper/results/`
- Format: JSON files named by job ID (UUID)
- Each file contains full transcription with timestamps

## 🔍 How to check results

### Option 1: Direct file access (on server)
```bash
# List all results
ls -la results/

# View specific result
cat results/<job-id>.json | jq
```

### Option 2: Use check script
```bash
python check_results.py
```

This shows:
- All saved transcriptions
- Creation time
- Language detected
- Text preview
- File size

## 📊 Understanding the response

When you transcribe audio, the API returns:
```json
{
  "text": "Your transcribed text here",
  "language": "en",
  "duration": 10.5,
  "segments": [...],
  "words": [...]
}
```

The same data is also saved to `results/<job-id>.json`

## ❓ Troubleshooting

### "No transcription saved"
- Check the `results/` folder exists
- Ensure the API returned 200 OK status
- Look for the job ID in the folder

### "Can't find my transcription"
- Results are saved with UUID names (e.g., `ba3fbffd-125b-438b-95fe-e240c2f9bdfe.json`)
- Use `python check_results.py` to list all results with previews
- Results are sorted by newest first

### Need to download results?
```bash
# Copy all results to local machine
scp user@server:path/to/lbrxWhisper/results/*.json ./my_results/
```