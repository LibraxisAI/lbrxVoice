#!/usr/bin/env python3
"""
Upload DIA MLX model to HuggingFace Hub
"""

import os
import json
from pathlib import Path
from huggingface_hub import HfApi, create_repo, upload_folder


def create_model_card(model_dir: Path) -> str:
    """Create model card for HuggingFace"""
    
    # Load model info
    with open(model_dir / "model_info.json", "r") as f:
        info = json.load(f)
        
    card_content = f"""---
language: en
license: apache-2.0
tags:
- text-to-speech
- tts
- mlx
- apple-silicon
- dialogue
- voice-cloning
library_name: mlx
---

# DIA 1.6B MLX

This is an MLX-optimized version of the [DIA 1.6B](https://huggingface.co/nari-labs/Dia-1.6B) text-to-speech model, 
specifically designed for Apple Silicon devices.

## Model Description

DIA is a 1.6B parameter text-to-speech model that directly generates highly realistic dialogue from a transcript. 
This MLX version provides optimized inference on Apple Silicon Macs.

### Key Features
- 🎭 Multi-speaker dialogue generation using `[S1]` and `[S2]` tags
- 😄 Non-verbal communication (laughs, coughs, sighs, etc.)
- 🎤 Voice cloning capabilities
- ⚡ Optimized for Apple Silicon with MLX

## Usage

```python
from dia_mlx import DiaMLX

# Initialize model
model = DiaMLX("LibraxisAI/dia-1.6b-mlx")
model.load_model()

# Generate speech
text = "[S1] Hello from DIA MLX! [S2] This runs great on Apple Silicon. [S1] (laughs) Amazing!"
audio_codes = model.generate(text)
audio_waveform = model.codes_to_audio(audio_codes)
```

## Model Architecture

- **Parameters**: {info.get('total_parameters', 'N/A'):,}
- **Encoder Layers**: {info.get('encoder_layers', 12)}
- **Decoder Layers**: {info.get('decoder_layers', 18)}
- **Format**: MLX (weights.npz)

## Requirements

- Apple Silicon Mac (M1/M2/M3)
- Python 3.8+
- MLX framework
- DAC (Descript Audio Codec) for audio decoding

## Installation

```bash
pip install mlx numpy soundfile
```

## Citation

If you use this model, please cite the original DIA paper:

```bibtex
@misc{{dia2024,
  title={{DIA: A 1.6B Parameter Text-to-Speech Model}},
  author={{Nari Labs}},
  year={{2024}},
  url={{https://github.com/nari-labs/dia}}
}}
```

## License

This model is licensed under the Apache 2.0 License.

## Acknowledgments

- Original DIA model by [Nari Labs](https://github.com/nari-labs)
- MLX conversion by [LibraxisAI](https://github.com/LibraxisAI)
"""
    
    return card_content


def upload_model_to_hf(
    model_dir: Path,
    repo_id: str = "LibraxisAI/dia-1.6b-mlx",
    private: bool = False
):
    """Upload MLX model to HuggingFace Hub"""
    
    print(f"📤 Uploading model to {repo_id}")
    
    # Initialize HF API
    api = HfApi()
    token = os.environ.get("HF_TOKEN")
    
    if not token:
        print("⚠️  HF_TOKEN not found. Please set it:")
        print("export HF_TOKEN='your_token_here'")
        return
    
    try:
        # Create repository
        print("Creating repository...")
        create_repo(
            repo_id=repo_id,
            token=token,
            private=private,
            exist_ok=True,
            repo_type="model"
        )
        
        # Create model card
        print("Creating model card...")
        model_card = create_model_card(model_dir)
        model_card_path = model_dir / "README.md"
        with open(model_card_path, "w") as f:
            f.write(model_card)
        
        # Create .gitattributes for LFS
        gitattributes = """*.npz filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
"""
        gitattributes_path = model_dir / ".gitattributes"
        with open(gitattributes_path, "w") as f:
            f.write(gitattributes)
        
        # Upload folder
        print("Uploading files...")
        api.upload_folder(
            folder_path=str(model_dir),
            repo_id=repo_id,
            token=token,
            commit_message="Upload DIA 1.6B MLX model"
        )
        
        print(f"\n✅ Model uploaded successfully!")
        print(f"🔗 View at: https://huggingface.co/{repo_id}")
        
    except Exception as e:
        print(f"❌ Error uploading model: {e}")


def main():
    """Main upload function"""
    
    model_dir = Path("./models/dia_mlx")
    
    if not model_dir.exists():
        print("❌ Model directory not found. Run conversion first:")
        print("  python dia_mlx_converter.py")
        return
        
    # Check required files
    required_files = ["weights.npz", "config.json", "model_info.json"]
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return
        
    # Upload to HuggingFace
    upload_model_to_hf(model_dir)


if __name__ == "__main__":
    main()