#!/usr/bin/env python3
"""
Simple DIA to MLX converter based on CSM approach
"""

import json
from pathlib import Path
import numpy as np

import mlx.core as mx
from safetensors import safe_open
from huggingface_hub import hf_hub_download


def download_and_convert():
    """Download DIA model and convert to MLX format"""
    
    print("🚀 DIA to MLX Converter")
    print("=" * 50)
    
    # 1. Download model files
    print("\n1. Downloading DIA model...")
    cache_dir = Path("./models/dia_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        model_path = hf_hub_download(
            repo_id="nari-labs/Dia-1.6B",
            filename="model.safetensors",
            cache_dir=str(cache_dir)
        )
        print(f"✅ Model downloaded: {model_path}")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("Trying alternative file...")
        model_path = hf_hub_download(
            repo_id="nari-labs/Dia-1.6B",
            filename="dia-v0_1.pth",
            cache_dir=str(cache_dir)
        )
    
    config_path = hf_hub_download(
        repo_id="nari-labs/Dia-1.6B",
        filename="config.json",
        cache_dir=str(cache_dir)
    )
    print(f"✅ Config downloaded: {config_path}")
    
    # 2. Load weights from safetensors
    print("\n2. Loading weights...")
    weights = {}
    
    if model_path.endswith('.safetensors'):
        with safe_open(model_path, framework="pt", device="cpu") as f:
            for key in f.keys():
                tensor = f.get_tensor(key)
                weights[key] = mx.array(tensor.numpy())
                print(f"  Loaded: {key} {tensor.shape}")
    else:
        # Handle .pth file
        import torch
        checkpoint = torch.load(model_path, map_location="cpu")
        if "model" in checkpoint:
            checkpoint = checkpoint["model"]
        
        for key, tensor in checkpoint.items():
            weights[key] = mx.array(tensor.numpy())
            print(f"  Loaded: {key} {tensor.shape}")
    
    print(f"\n✅ Loaded {len(weights)} weight tensors")
    
    # 3. Load config
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # 4. Save MLX format
    output_dir = Path("./models/dia_mlx")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save weights using mx.savez
    weights_path = output_dir / "weights.npz"
    print(f"\n3. Saving weights to {weights_path}...")
    mx.savez(str(weights_path), **weights)
    
    # Save config
    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    # Create model info
    total_params = sum(w.size for w in weights.values())
    info = {
        "model_type": "dia_tts",
        "version": "1.6B",
        "format": "mlx",
        "total_parameters": int(total_params),
        "weight_keys": len(weights),
        "converted_from": "nari-labs/Dia-1.6B"
    }
    
    info_path = output_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)
    
    print(f"\n✅ Conversion complete!")
    print(f"   Model saved to: {output_dir}")
    print(f"   Total parameters: {total_params:,}")
    print(f"   Weight keys: {len(weights)}")
    
    # List some weight keys for verification
    print("\n📋 Sample weight keys:")
    for i, key in enumerate(list(weights.keys())[:10]):
        print(f"   - {key}")
    
    return output_dir


if __name__ == "__main__":
    download_and_convert()