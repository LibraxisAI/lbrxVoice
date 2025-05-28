#!/usr/bin/env python3
"""
Convert DIA model from safetensors to pure MLX format
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

import mlx.core as mx
import mlx.nn as nn
from safetensors import safe_open
from huggingface_hub import hf_hub_download


class DiaMLXConverter:
    """Convert DIA PyTorch model to MLX"""
    
    def __init__(self):
        self.weight_map = {
            # Text embeddings
            "model.encoder.text_encoder.embed_tokens.weight": "text_embeddings.weight",
            
            # Audio embeddings (9 codebooks)
            **{f"model.decoder.audio_embeddings.{i}.weight": f"audio_embeddings.{i}.weight" 
               for i in range(9)},
            
            # Position embeddings
            "model.encoder.pos_embedding.weight": "position_embeddings.weight",
            
            # Encoder layers (12 layers)
            **self._create_encoder_mapping(),
            
            # Decoder layers (18 layers)
            **self._create_decoder_mapping(),
            
            # Output heads
            "model.lm_head.weight": "text_head.weight",
            **{f"model.audio_heads.{i}.weight": f"audio_heads.{i}.weight" 
               for i in range(9)},
        }
    
    def _create_encoder_mapping(self) -> Dict[str, str]:
        """Create mapping for encoder layers"""
        mapping = {}
        for i in range(12):
            prefix = f"model.encoder.layers.{i}"
            mlx_prefix = f"encoder_blocks.{i}"
            
            # Self attention
            mapping.update({
                f"{prefix}.self_attn.q_proj.weight": f"{mlx_prefix}.attention.q_proj.weight",
                f"{prefix}.self_attn.k_proj.weight": f"{mlx_prefix}.attention.k_proj.weight",
                f"{prefix}.self_attn.v_proj.weight": f"{mlx_prefix}.attention.v_proj.weight",
                f"{prefix}.self_attn.o_proj.weight": f"{mlx_prefix}.attention.o_proj.weight",
                
                # FFN
                f"{prefix}.mlp.fc1.weight": f"{mlx_prefix}.feed_forward.layers.0.weight",
                f"{prefix}.mlp.fc2.weight": f"{mlx_prefix}.feed_forward.layers.2.weight",
                
                # Layer norms
                f"{prefix}.input_layernorm.weight": f"{mlx_prefix}.ln1.weight",
                f"{prefix}.post_attention_layernorm.weight": f"{mlx_prefix}.ln2.weight",
            })
        
        # Final layer norm
        mapping["model.encoder.layer_norm.weight"] = "encoder_ln_f.weight"
        
        return mapping
    
    def _create_decoder_mapping(self) -> Dict[str, str]:
        """Create mapping for decoder layers"""
        mapping = {}
        for i in range(18):
            prefix = f"model.decoder.layers.{i}"
            mlx_prefix = f"decoder_blocks.{i}"
            
            # Self attention
            mapping.update({
                f"{prefix}.self_attn.q_proj.weight": f"{mlx_prefix}.self_attention.q_proj.weight",
                f"{prefix}.self_attn.k_proj.weight": f"{mlx_prefix}.self_attention.k_proj.weight",
                f"{prefix}.self_attn.v_proj.weight": f"{mlx_prefix}.self_attention.v_proj.weight",
                f"{prefix}.self_attn.o_proj.weight": f"{mlx_prefix}.self_attention.o_proj.weight",
                
                # Cross attention
                f"{prefix}.cross_attn.q_proj.weight": f"{mlx_prefix}.cross_attention.q_proj.weight",
                f"{prefix}.cross_attn.k_proj.weight": f"{mlx_prefix}.cross_attention.k_proj.weight",
                f"{prefix}.cross_attn.v_proj.weight": f"{mlx_prefix}.cross_attention.v_proj.weight",
                f"{prefix}.cross_attn.o_proj.weight": f"{mlx_prefix}.cross_attention.o_proj.weight",
                
                # FFN
                f"{prefix}.mlp.fc1.weight": f"{mlx_prefix}.feed_forward.layers.0.weight",
                f"{prefix}.mlp.fc2.weight": f"{mlx_prefix}.feed_forward.layers.2.weight",
                
                # Layer norms
                f"{prefix}.input_layernorm.weight": f"{mlx_prefix}.ln1.weight",
                f"{prefix}.post_attention_layernorm.weight": f"{mlx_prefix}.ln2.weight",
                f"{prefix}.cross_attn_layernorm.weight": f"{mlx_prefix}.ln_cross.weight",
            })
        
        # Final layer norm
        mapping["model.decoder.layer_norm.weight"] = "decoder_ln_f.weight"
        
        return mapping
    
    def load_safetensors(self, model_path: Path) -> Dict[str, np.ndarray]:
        """Load weights from safetensors file"""
        weights = {}
        
        with safe_open(model_path, framework="pt", device="cpu") as f:
            for key in f.keys():
                tensor = f.get_tensor(key)
                weights[key] = tensor.numpy()
                
        print(f"Loaded {len(weights)} tensors from safetensors")
        return weights
    
    def convert_weights(self, pt_weights: Dict[str, np.ndarray]) -> Dict[str, mx.array]:
        """Convert PyTorch weights to MLX format"""
        mlx_weights = {}
        
        for pt_name, mlx_name in self.weight_map.items():
            if pt_name in pt_weights:
                # Convert to MLX array
                weight = pt_weights[pt_name]
                
                # Handle any necessary transpositions
                if "q_proj" in mlx_name or "k_proj" in mlx_name or "v_proj" in mlx_name:
                    # Attention weights might need reshaping
                    pass  # Keep original shape for now
                
                mlx_weights[mlx_name] = mx.array(weight)
                print(f"Converted {pt_name} -> {mlx_name}: {weight.shape}")
            else:
                print(f"Warning: Missing weight {pt_name}")
        
        # Check for unmapped weights
        unmapped = set(pt_weights.keys()) - set(self.weight_map.keys())
        if unmapped:
            print(f"\nUnmapped weights ({len(unmapped)}):")
            for name in sorted(unmapped)[:10]:
                print(f"  - {name}")
            if len(unmapped) > 10:
                print(f"  ... and {len(unmapped) - 10} more")
        
        return mlx_weights
    
    def convert_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DIA config to MLX format"""
        mlx_config = {
            # Model architecture
            "model_type": "dia_mlx",
            "vocab_size": config.get("vocab_size", 32000),
            "hidden_size": config.get("encoder_hidden_size", 1024),
            "encoder_layers": config.get("encoder_layers", 12),
            "decoder_layers": config.get("decoder_layers", 18),
            "encoder_hidden_size": config.get("encoder_hidden_size", 1024),
            "decoder_hidden_size": config.get("decoder_hidden_size", 2048),
            "num_attention_heads": config.get("num_attention_heads", 16),
            "intermediate_size": config.get("intermediate_size", 4096),
            "max_position_embeddings": config.get("max_position_embeddings", 4096),
            
            # Audio settings
            "audio_vocab_size": config.get("audio_vocab_size", 4096),
            "num_audio_codebooks": config.get("num_codebooks", 9),
            "audio_eos_token_id": config.get("audio_eos_token_id", 2048),
            
            # Generation settings
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 50,
            
            # Tokenizer settings
            "pad_token_id": config.get("pad_token_id", 0),
            "bos_token_id": config.get("bos_token_id", 1),
            "eos_token_id": config.get("eos_token_id", 2),
        }
        
        return mlx_config


def main():
    print("DIA to MLX Converter")
    print("=" * 50)
    
    # Download model files
    print("\n1. Downloading model files...")
    model_path = hf_hub_download(
        repo_id="nari-labs/Dia-1.6B",
        filename="model.safetensors",
        cache_dir="./models/dia_download"
    )
    
    config_path = hf_hub_download(
        repo_id="nari-labs/Dia-1.6B",
        filename="config.json",
        cache_dir="./models/dia_download"
    )
    
    # Load config
    print("\n2. Loading configuration...")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Initialize converter
    converter = DiaMLXConverter()
    
    # Load weights
    print("\n3. Loading safetensors weights...")
    pt_weights = converter.load_safetensors(model_path)
    
    # Convert weights
    print("\n4. Converting weights to MLX...")
    mlx_weights = converter.convert_weights(pt_weights)
    
    # Convert config
    print("\n5. Converting configuration...")
    mlx_config = converter.convert_config(config)
    
    # Save MLX model
    print("\n6. Saving MLX model...")
    output_dir = Path("./models/dia_mlx")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save weights
    weights_path = output_dir / "weights.npz"
    mx.save(str(weights_path), mlx_weights)
    print(f"Saved weights to {weights_path}")
    
    # Save config
    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(mlx_config, f, indent=2)
    print(f"Saved config to {config_path}")
    
    # Save model info
    info = {
        "model_type": "dia_tts",
        "version": "1.6B",
        "format": "mlx",
        "converted_from": "nari-labs/Dia-1.6B",
        "total_parameters": sum(w.size for w in mlx_weights.values()),
        "encoder_layers": mlx_config["encoder_layers"],
        "decoder_layers": mlx_config["decoder_layers"],
    }
    
    info_path = output_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)
    
    print(f"\n✅ Conversion complete!")
    print(f"Model saved to: {output_dir}")
    print(f"Total parameters: {info['total_parameters']:,}")


if __name__ == "__main__":
    main()