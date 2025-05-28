"""
MLX implementation of DIA TTS model
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

import mlx
import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_map

from ..common.config import config as global_config


class DiaMLXConfig:
    """Configuration for DIA MLX model"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        # Model architecture
        self.vocab_size = config_dict.get("vocab_size", 32000)
        self.hidden_size = config_dict.get("hidden_size", 2048)
        self.num_hidden_layers = config_dict.get("num_hidden_layers", 24)
        self.num_attention_heads = config_dict.get("num_attention_heads", 16)
        self.intermediate_size = config_dict.get("intermediate_size", 8192)
        self.max_position_embeddings = config_dict.get("max_position_embeddings", 4096)
        
        # Audio settings
        self.audio_vocab_size = config_dict.get("audio_vocab_size", 4096)
        self.num_audio_codebooks = config_dict.get("num_audio_codebooks", 9)
        self.audio_eos_token_id = config_dict.get("audio_eos_token_id", 2048)
        
        # Generation settings
        self.temperature = config_dict.get("temperature", 0.8)
        self.top_p = config_dict.get("top_p", 0.95)
        self.top_k = config_dict.get("top_k", None)


class MultiHeadAttention(nn.Module):
    """Multi-head attention for DIA"""
    
    def __init__(self, config: DiaMLXConfig):
        super().__init__()
        self.num_heads = config.num_attention_heads
        self.hidden_size = config.hidden_size
        self.head_dim = self.hidden_size // self.num_heads
        
        self.q_proj = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.o_proj = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        
    def __call__(self, x: mx.array, mask: Optional[mx.array] = None) -> mx.array:
        B, L, D = x.shape
        
        # Project to Q, K, V
        q = self.q_proj(x).reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        k = self.k_proj(x).reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        v = self.v_proj(x).reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # Scaled dot-product attention
        scores = (q @ k.transpose(0, 1, 3, 2)) / mx.sqrt(mx.array(self.head_dim))
        
        if mask is not None:
            scores = scores + mask
            
        attn_weights = mx.softmax(scores, axis=-1)
        attn_output = attn_weights @ v
        
        # Reshape and project
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(B, L, D)
        return self.o_proj(attn_output)


class DiaMLXBlock(nn.Module):
    """Transformer block for DIA"""
    
    def __init__(self, config: DiaMLXConfig):
        super().__init__()
        self.attention = MultiHeadAttention(config)
        self.feed_forward = nn.Sequential(
            nn.Linear(config.hidden_size, config.intermediate_size),
            nn.GELU(),
            nn.Linear(config.intermediate_size, config.hidden_size)
        )
        self.ln1 = nn.LayerNorm(config.hidden_size)
        self.ln2 = nn.LayerNorm(config.hidden_size)
        
    def __call__(self, x: mx.array, mask: Optional[mx.array] = None) -> mx.array:
        # Attention with residual
        attn_out = self.attention(self.ln1(x), mask)
        x = x + attn_out
        
        # FFN with residual
        ffn_out = self.feed_forward(self.ln2(x))
        x = x + ffn_out
        
        return x


class DiaMLXModel(nn.Module):
    """MLX implementation of DIA TTS model"""
    
    def __init__(self, config: DiaMLXConfig):
        super().__init__()
        self.config = config
        
        # Embeddings
        self.text_embeddings = nn.Embedding(config.vocab_size, config.hidden_size)
        self.audio_embeddings = nn.ModuleList([
            nn.Embedding(config.audio_vocab_size, config.hidden_size)
            for _ in range(config.num_audio_codebooks)
        ])
        self.position_embeddings = nn.Embedding(config.max_position_embeddings, config.hidden_size)
        
        # Transformer blocks
        self.blocks = nn.ModuleList([
            DiaMLXBlock(config) for _ in range(config.num_hidden_layers)
        ])
        
        # Output heads
        self.ln_f = nn.LayerNorm(config.hidden_size)
        self.text_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.audio_heads = nn.ModuleList([
            nn.Linear(config.hidden_size, config.audio_vocab_size, bias=False)
            for _ in range(config.num_audio_codebooks)
        ])
        
    def embed_text(self, text_ids: mx.array) -> mx.array:
        """Embed text tokens"""
        return self.text_embeddings(text_ids)
        
    def embed_audio(self, audio_codes: mx.array) -> mx.array:
        """Embed audio codes from multiple codebooks"""
        # audio_codes shape: [batch, codebooks, sequence]
        embedded = []
        for i in range(self.config.num_audio_codebooks):
            embedded.append(self.audio_embeddings[i](audio_codes[:, i, :]))
        # Sum embeddings from all codebooks
        return mx.sum(mx.stack(embedded, axis=0), axis=0)
        
    def __call__(self, 
                 text_ids: Optional[mx.array] = None,
                 audio_codes: Optional[mx.array] = None,
                 use_cache: bool = False) -> Dict[str, mx.array]:
        """Forward pass"""
        
        # Get embeddings
        if text_ids is not None and audio_codes is not None:
            text_embeds = self.embed_text(text_ids)
            audio_embeds = self.embed_audio(audio_codes)
            hidden_states = mx.concatenate([text_embeds, audio_embeds], axis=1)
        elif text_ids is not None:
            hidden_states = self.embed_text(text_ids)
        elif audio_codes is not None:
            hidden_states = self.embed_audio(audio_codes)
        else:
            raise ValueError("Either text_ids or audio_codes must be provided")
            
        # Add position embeddings
        seq_len = hidden_states.shape[1]
        position_ids = mx.arange(seq_len)
        hidden_states = hidden_states + self.position_embeddings(position_ids)
        
        # Create causal mask
        mask = mx.triu(mx.full((seq_len, seq_len), float('-inf')), k=1)
        
        # Apply transformer blocks
        for block in self.blocks:
            hidden_states = block(hidden_states, mask)
            
        # Final layer norm
        hidden_states = self.ln_f(hidden_states)
        
        # Get logits
        text_logits = self.text_head(hidden_states)
        audio_logits = [head(hidden_states) for head in self.audio_heads]
        
        return {
            "text_logits": text_logits,
            "audio_logits": mx.stack(audio_logits, axis=1),  # [batch, codebooks, seq, vocab]
            "hidden_states": hidden_states
        }


class DiaMLX:
    """High-level interface for DIA MLX model"""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = global_config.dia_model_path
            
        self.model_path = Path(model_path)
        self.config = None
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """Load model weights and configuration"""
        print(f"Loading DIA MLX model from {self.model_path}")
        
        # Load config
        config_path = self.model_path / "config.json"
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        self.config = DiaMLXConfig(config_dict)
        
        # Initialize model
        self.model = DiaMLXModel(self.config)
        
        # Load weights
        weights_path = self.model_path / "weights.npz"
        weights = mx.load(str(weights_path))
        self.model.load_weights(weights)
        
        print("Model loaded successfully")
        
    def generate(self, 
                 text: str,
                 temperature: float = None,
                 top_p: float = None,
                 max_length: int = 2048) -> mx.array:
        """Generate audio from text"""
        
        if self.model is None:
            self.load_model()
            
        # TODO: Implement tokenization and generation logic
        # This is a placeholder - actual implementation needs proper tokenization
        # and generation strategy specific to DIA
        
        print(f"Generating audio for text: {text[:50]}...")
        
        # For now, return dummy audio codes
        # Real implementation would:
        # 1. Tokenize text with proper [S1], [S2] tags
        # 2. Generate audio codes autoregressively
        # 3. Convert codes to audio waveform
        
        dummy_codes = mx.zeros((1, self.config.num_audio_codebooks, 1000))
        return dummy_codes
        
    def codes_to_audio(self, audio_codes: mx.array, sample_rate: int = 44100) -> np.ndarray:
        """Convert audio codes to waveform"""
        # TODO: Implement audio decoding
        # This requires the DAC (Descript Audio Codec) decoder
        
        # For now, return dummy audio
        duration = audio_codes.shape[-1] / 86  # ~86 codes per second
        samples = int(duration * sample_rate)
        return np.zeros(samples, dtype=np.float32)