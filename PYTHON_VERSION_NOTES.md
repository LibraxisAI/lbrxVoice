# Python Version Compatibility Notes

## Current Status
- **Project requirement**: Python >= 3.11
- **UV will handle**: Automatic Python version management

## Component Compatibility

### ✅ Works on Python 3.11+
- MLX and all MLX-based components
- Whisper MLX
- Our custom XTTS MLX implementation
- All core functionality

### ⚠️ Python Version Conflicts
- **CSM-MLX**: May require Python 3.13 (found .venv_csm with 3.13)
- **Coqui TTS library**: Requires Python < 3.12 (not compatible with 3.12+)

## Solution
We use our custom XTTS MLX implementation instead of the coqui library. This gives us:
- Full Polish TTS support
- MLX optimization for Apple Silicon
- No Python version conflicts
- Works with Python 3.11, 3.12, 3.13+

## UV Workflow
```bash
# UV will automatically use the right Python version based on pyproject.toml
uv sync
uv run python run_ultimate_tui.py
```

UV handles everything - no need to worry about Python versions!