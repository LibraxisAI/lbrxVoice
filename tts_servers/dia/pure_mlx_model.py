"""
Pure MLX implementation of DIA TTS model
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

import mlx
import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten, tree_map


class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding for attention"""
    
    def __init__(self, dims: int, max_position_embeddings: int = 4096):
        super().__init__()
        self.dims = dims
        self.max_position_embeddings = max_position_embeddings
        
        inv_freq = 1.0 / (10000 ** (mx.arange(0, dims, 2) / dims))
        self.inv_freq = inv_freq
        
    def __call__(self, x: mx.array, offset: int = 0) -> mx.array:
        seq_len = x.shape[1]
        t = mx.arange(offset, offset + seq_len)
        freqs = mx.outer(t, self.inv_freq)
        emb = mx.concatenate([freqs, freqs], axis=-1)
        cos = mx.cos(emb)
        sin = mx.sin(emb)
        return cos, sin


def apply_rotary_emb(q: mx.array, k: mx.array, cos: mx.array, sin: mx.array) -> Tuple[mx.array, mx.array]:
    """Apply rotary embeddings to query and key"""
    def rotate_half(x):
        x1, x2 = mx.split(x, 2, axis=-1)
        return mx.concatenate([-x2, x1], axis=-1)
    
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class DiaAttention(nn.Module):
    """Multi-head attention with rotary embeddings"""
    
    def __init__(self, hidden_size: int, num_heads: int, is_cross_attention: bool = False):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.is_cross_attention = is_cross_attention
        
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.o_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        
        if not is_cross_attention:
            self.rotary_emb = RotaryEmbedding(self.head_dim)
        
    def __call__(
        self, 
        x: mx.array, 
        encoder_hidden_states: Optional[mx.array] = None,
        mask: Optional[mx.array] = None,
        cache: Optional[Tuple[mx.array, mx.array]] = None
    ) -> Tuple[mx.array, Optional[Tuple[mx.array, mx.array]]]:
        B, L, D = x.shape
        
        # Compute Q, K, V
        q = self.q_proj(x)
        
        if self.is_cross_attention and encoder_hidden_states is not None:
            k = self.k_proj(encoder_hidden_states)
            v = self.v_proj(encoder_hidden_states)
        else:
            k = self.k_proj(x)
            v = self.v_proj(x)
        
        # Reshape for multi-head attention
        q = q.reshape(B, -1, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        k = k.reshape(B, -1, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        v = v.reshape(B, -1, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # Apply rotary embeddings (only for self-attention)
        if not self.is_cross_attention:
            offset = 0
            if cache is not None:
                offset = cache[0].shape[2]
            cos, sin = self.rotary_emb(q, offset)
            q, k = apply_rotary_emb(q, k, cos, sin)
        
        # Update cache if provided
        if cache is not None:
            k_cache, v_cache = cache
            k = mx.concatenate([k_cache, k], axis=2)
            v = mx.concatenate([v_cache, v], axis=2)
            cache = (k, v)
        
        # Scaled dot-product attention
        scores = (q @ k.transpose(0, 1, 3, 2)) / mx.sqrt(mx.array(self.head_dim))
        
        if mask is not None:
            scores = scores + mask
            
        attn = mx.softmax(scores, axis=-1)
        out = attn @ v
        
        # Reshape and project
        out = out.transpose(0, 2, 1, 3).reshape(B, L, D)
        out = self.o_proj(out)
        
        return out, cache


class DiaEncoderLayer(nn.Module):
    """Transformer encoder layer"""
    
    def __init__(self, hidden_size: int, num_heads: int, intermediate_size: int):
        super().__init__()
        self.attention = DiaAttention(hidden_size, num_heads)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_size, intermediate_size),
            nn.GELU(),
            nn.Linear(intermediate_size, hidden_size)
        )
        self.ln1 = nn.LayerNorm(hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
        
    def __call__(self, x: mx.array, mask: Optional[mx.array] = None) -> mx.array:
        # Self-attention with residual
        attn_out, _ = self.attention(self.ln1(x), mask=mask)
        x = x + attn_out
        
        # FFN with residual
        x = x + self.feed_forward(self.ln2(x))
        
        return x


class DiaDecoderLayer(nn.Module):
    """Transformer decoder layer with cross-attention"""
    
    def __init__(self, hidden_size: int, num_heads: int, intermediate_size: int):
        super().__init__()
        self.self_attention = DiaAttention(hidden_size, num_heads)
        self.cross_attention = DiaAttention(hidden_size, num_heads, is_cross_attention=True)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_size, intermediate_size),
            nn.GELU(),
            nn.Linear(intermediate_size, hidden_size)
        )
        self.ln1 = nn.LayerNorm(hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)
        self.ln_cross = nn.LayerNorm(hidden_size)
        
    def __call__(
        self, 
        x: mx.array, 
        encoder_hidden_states: mx.array,
        mask: Optional[mx.array] = None,
        encoder_mask: Optional[mx.array] = None,
        cache: Optional[Dict[str, Tuple[mx.array, mx.array]]] = None
    ) -> Tuple[mx.array, Optional[Dict[str, Tuple[mx.array, mx.array]]]]:
        
        # Self-attention with residual
        self_cache = cache.get("self") if cache else None
        attn_out, new_self_cache = self.self_attention(
            self.ln1(x), mask=mask, cache=self_cache
        )
        x = x + attn_out
        
        # Cross-attention with residual
        cross_out, _ = self.cross_attention(
            self.ln_cross(x), 
            encoder_hidden_states=encoder_hidden_states,
            mask=encoder_mask
        )
        x = x + cross_out
        
        # FFN with residual
        x = x + self.feed_forward(self.ln2(x))
        
        # Update cache
        new_cache = None
        if cache is not None or new_self_cache is not None:
            new_cache = {"self": new_self_cache}
        
        return x, new_cache


class DiaMLXModel(nn.Module):
    """Pure MLX implementation of DIA TTS model"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        # Text embeddings
        self.text_embeddings = nn.Embedding(config["vocab_size"], config["encoder_hidden_size"])
        
        # Audio embeddings (multiple codebooks)
        self.audio_embeddings = nn.ModuleList([
            nn.Embedding(config["audio_vocab_size"], config["decoder_hidden_size"])
            for _ in range(config["num_audio_codebooks"])
        ])
        
        # Position embeddings
        self.position_embeddings = nn.Embedding(
            config["max_position_embeddings"], 
            config["encoder_hidden_size"]
        )
        
        # Encoder
        self.encoder_blocks = nn.ModuleList([
            DiaEncoderLayer(
                config["encoder_hidden_size"],
                config["num_attention_heads"],
                config["intermediate_size"]
            )
            for _ in range(config["encoder_layers"])
        ])
        self.encoder_ln_f = nn.LayerNorm(config["encoder_hidden_size"])
        
        # Decoder
        self.decoder_blocks = nn.ModuleList([
            DiaDecoderLayer(
                config["decoder_hidden_size"],
                config["num_attention_heads"],
                config["intermediate_size"]
            )
            for _ in range(config["decoder_layers"])
        ])
        self.decoder_ln_f = nn.LayerNorm(config["decoder_hidden_size"])
        
        # Projection layer if encoder/decoder dimensions differ
        if config["encoder_hidden_size"] != config["decoder_hidden_size"]:
            self.encoder_to_decoder_proj = nn.Linear(
                config["encoder_hidden_size"],
                config["decoder_hidden_size"]
            )
        else:
            self.encoder_to_decoder_proj = None
        
        # Output heads
        self.text_head = nn.Linear(config["decoder_hidden_size"], config["vocab_size"], bias=False)
        self.audio_heads = nn.ModuleList([
            nn.Linear(config["decoder_hidden_size"], config["audio_vocab_size"], bias=False)
            for _ in range(config["num_audio_codebooks"])
        ])
        
    def encode_text(self, text_ids: mx.array) -> mx.array:
        """Encode text input"""
        # Get embeddings
        hidden_states = self.text_embeddings(text_ids)
        
        # Add position embeddings
        seq_len = text_ids.shape[1]
        position_ids = mx.arange(seq_len)
        hidden_states = hidden_states + self.position_embeddings(position_ids)
        
        # Create causal mask for encoder
        mask = mx.triu(mx.full((seq_len, seq_len), float('-inf')), k=1)
        
        # Apply encoder layers
        for block in self.encoder_blocks:
            hidden_states = block(hidden_states, mask)
            
        # Final layer norm
        hidden_states = self.encoder_ln_f(hidden_states)
        
        return hidden_states
        
    def decode_audio(
        self, 
        encoder_hidden_states: mx.array,
        audio_codes: Optional[mx.array] = None,
        cache: Optional[Dict[int, Dict[str, Tuple[mx.array, mx.array]]]] = None
    ) -> Tuple[Dict[str, mx.array], Optional[Dict]]:
        """Decode audio from encoder hidden states"""
        
        # Project encoder hidden states if needed
        if self.encoder_to_decoder_proj is not None:
            encoder_hidden_states = self.encoder_to_decoder_proj(encoder_hidden_states)
        
        # Initialize decoder input
        if audio_codes is not None:
            # Sum embeddings from all codebooks
            hidden_states = mx.zeros_like(self.audio_embeddings[0](audio_codes[:, 0, :]))
            for i in range(self.config["num_audio_codebooks"]):
                hidden_states = hidden_states + self.audio_embeddings[i](audio_codes[:, i, :])
        else:
            # Start with zeros for generation
            batch_size = encoder_hidden_states.shape[0]
            hidden_states = mx.zeros((batch_size, 1, self.config["decoder_hidden_size"]))
        
        # Create causal mask for decoder
        seq_len = hidden_states.shape[1]
        mask = mx.triu(mx.full((seq_len, seq_len), float('-inf')), k=1)
        
        # Apply decoder layers
        new_cache = {}
        for i, block in enumerate(self.decoder_blocks):
            layer_cache = cache.get(i) if cache else None
            hidden_states, new_layer_cache = block(
                hidden_states, 
                encoder_hidden_states,
                mask=mask,
                cache=layer_cache
            )
            if new_layer_cache is not None:
                new_cache[i] = new_layer_cache
        
        # Final layer norm
        hidden_states = self.decoder_ln_f(hidden_states)
        
        # Get logits for all codebooks
        audio_logits = [head(hidden_states) for head in self.audio_heads]
        
        return {
            "audio_logits": mx.stack(audio_logits, axis=1),  # [batch, codebooks, seq, vocab]
            "hidden_states": hidden_states
        }, new_cache if new_cache else None
        
    def __call__(
        self,
        text_ids: mx.array,
        audio_codes: Optional[mx.array] = None,
        cache: Optional[Dict] = None
    ) -> Tuple[Dict[str, mx.array], Optional[Dict]]:
        """Forward pass"""
        
        # Encode text
        encoder_hidden_states = self.encode_text(text_ids)
        
        # Decode audio
        outputs, new_cache = self.decode_audio(
            encoder_hidden_states, 
            audio_codes, 
            cache
        )
        
        return outputs, new_cache


class DiaMLX:
    """High-level interface for pure MLX DIA model"""
    
    def __init__(self, model_path: str = "./models/dia_mlx"):
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
            self.config = json.load(f)
        
        # Initialize model
        self.model = DiaMLXModel(self.config)
        
        # Load weights
        weights_path = self.model_path / "weights.npz"
        weights = mx.load(str(weights_path))
        
        # Set weights
        self.model.load_weights(list(weights.items()))
        
        print("Model loaded successfully")
        
    def generate(
        self,
        text: str,
        max_length: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.95,
        top_k: int = 50
    ) -> mx.array:
        """Generate audio codes from text"""
        
        if self.model is None:
            self.load_model()
        
        # TODO: Implement proper tokenization
        # For now, create dummy text IDs
        text_ids = mx.array([[1] * min(len(text.split()), 512)])  # Dummy tokenization
        
        # Encode text
        encoder_states = self.model.encode_text(text_ids)
        
        # Generate audio codes autoregressively
        audio_codes = []
        cache = None
        
        for step in range(max_length):
            # Decode next step
            outputs, cache = self.model.decode_audio(
                encoder_states,
                audio_codes=None,  # Use cache for continuation
                cache=cache
            )
            
            # Sample from logits
            logits = outputs["audio_logits"][:, :, -1, :]  # Get last timestep
            
            # Apply temperature
            logits = logits / temperature
            
            # Apply top-k/top-p sampling
            next_codes = []
            for cb in range(self.config["num_audio_codebooks"]):
                cb_logits = logits[:, cb, :]
                
                # Top-k filtering
                if top_k > 0:
                    top_k_logits, top_k_indices = mx.topk(cb_logits, k=top_k)
                    cb_logits = mx.full_like(cb_logits, float('-inf'))
                    cb_logits = mx.scatter(cb_logits, top_k_indices, top_k_logits, axis=-1)
                
                # Sample
                probs = mx.softmax(cb_logits, axis=-1)
                next_code = mx.random.categorical(mx.log(probs))
                next_codes.append(next_code)
            
            # Stack codes for all codebooks
            next_codes = mx.stack(next_codes, axis=1)
            audio_codes.append(next_codes)
            
            # Check for EOS
            if mx.any(next_codes == self.config["audio_eos_token_id"]):
                break
        
        # Stack all generated codes
        audio_codes = mx.concatenate(audio_codes, axis=-1)
        
        return audio_codes
        
    def codes_to_audio(self, audio_codes: mx.array, sample_rate: int = 44100) -> np.ndarray:
        """Convert audio codes to waveform using DAC decoder"""
        # TODO: Implement DAC decoder in MLX
        # For now, return dummy audio
        duration = audio_codes.shape[-1] / 86  # ~86 codes per second
        samples = int(duration * sample_rate)
        return np.zeros(samples, dtype=np.float32)