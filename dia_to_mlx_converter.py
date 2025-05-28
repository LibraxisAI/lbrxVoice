#!/usr/bin/env python3
"""
Convert DIA model from safetensors to MLX format
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any

import torch
import mlx
import mlx.core as mx
import mlx.nn as nn
import numpy as np
from safetensors import safe_open
from huggingface_hub import snapshot_download
from transformers import AutoConfig


def download_dia_model(model_id: str = "nari-labs/Dia-1.6B", cache_dir: str = "./models/dia") -> Path:
    """Download DIA model from Hugging Face"""
    print(f"Downloading {model_id} from Hugging Face...")
    
    # Set HF token if available
    hf_token = os.environ.get("HF_TOKEN")
    
    model_path = snapshot_download(
        repo_id=model_id,
        cache_dir=cache_dir,
        token=hf_token,
        allow_patterns=["*.safetensors", "*.json", "*.txt", "config.json"]
    )
    
    print(f"Model downloaded to: {model_path}")
    return Path(model_path)


def load_safetensors_weights(model_path: Path) -> Dict[str, np.ndarray]:
    """Load weights from safetensors files"""
    weights = {}
    
    # Find all safetensors files
    safetensor_files = list(model_path.glob("*.safetensors"))
    
    if not safetensor_files:
        raise FileNotFoundError(f"No safetensors files found in {model_path}")
    
    print(f"Found {len(safetensor_files)} safetensors files")
    
    for file_path in safetensor_files:
        print(f"Loading {file_path.name}...")
        with safe_open(file_path, framework="pt", device="cpu") as f:
            for key in f.keys():
                tensor = f.get_tensor(key)
                weights[key] = tensor.numpy()
                
    print(f"Loaded {len(weights)} weight tensors")
    return weights


def convert_weights_to_mlx(weights: Dict[str, np.ndarray]) -> Dict[str, mx.array]:
    """Convert numpy weights to MLX arrays"""
    mlx_weights = {}
    
    for name, weight in weights.items():
        # Convert to MLX array
        mlx_weights[name] = mx.array(weight)
        print(f"Converted {name}: {weight.shape} -> {mlx_weights[name].shape}")
    
    return mlx_weights


def save_mlx_model(mlx_weights: Dict[str, mx.array], config: Dict[str, Any], output_dir: Path):
    """Save MLX model weights and config"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save weights in MLX format
    weights_path = output_dir / "weights.npz"
    print(f"Saving MLX weights to {weights_path}...")
    mx.save(str(weights_path), mlx_weights)
    
    # Save config
    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Saved config to {config_path}")
    
    # Create model info
    model_info = {
        "model_type": "dia_tts",
        "version": "1.6B",
        "format": "mlx",
        "weights_file": "weights.npz",
        "config_file": "config.json"
    }
    
    info_path = output_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(model_info, f, indent=2)
    print(f"Saved model info to {info_path}")


def main():
    # Download model
    model_path = download_dia_model()
    
    # Load config
    config_path = model_path / "config.json"
    if not config_path.exists():
        # Try to find config.json in subdirectories
        config_files = list(model_path.rglob("config.json"))
        if config_files:
            config_path = config_files[0]
        else:
            raise FileNotFoundError(f"No config.json found in {model_path}")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    print(f"Loaded config from {config_path}")
    
    # Load weights
    weights = load_safetensors_weights(model_path)
    
    # Convert to MLX
    mlx_weights = convert_weights_to_mlx(weights)
    
    # Save MLX model
    output_dir = Path("./models/dia_mlx")
    save_mlx_model(mlx_weights, config, output_dir)
    
    print(f"\nConversion complete! MLX model saved to {output_dir}")
    print("\nModel structure:")
    print(f"- Total parameters: {sum(w.size for w in mlx_weights.values()):,}")
    print(f"- Number of layers: {len([k for k in mlx_weights.keys() if 'layer' in k])}")


if __name__ == "__main__":
    main()