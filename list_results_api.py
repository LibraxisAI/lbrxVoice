#!/usr/bin/env python3
"""
Simple API endpoint to list transcription results
Add this to whisper_servers/batch/api.py
"""

# Add this endpoint to the existing api.py file:

"""
@app.get("/v1/results")
async def list_results():
    '''List all transcription results'''
    from pathlib import Path
    import json
    
    results_dir = Path("results")
    results = []
    
    for json_file in results_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            results.append({
                "job_id": json_file.stem,
                "filename": json_file.name,
                "created": json_file.stat().st_mtime,
                "size_bytes": json_file.stat().st_size,
                "text_preview": data.get('text', '')[:100],
                "language": data.get('language', 'unknown'),
                "duration": data.get('duration', 0)
            })
        except:
            pass
    
    # Sort by creation time, newest first
    results.sort(key=lambda x: x['created'], reverse=True)
    
    return {
        "count": len(results),
        "results_directory": str(results_dir.absolute()),
        "results": results
    }
"""

print("Add the above endpoint to whisper_servers/batch/api.py")
print("\nThen users can check results at: http://0.0.0.0:8123/v1/results")