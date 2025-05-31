#!/usr/bin/env python3
"""
LLM Configuration with environment variable support
Supports LM Studio, OpenRouter, and Dragon endpoints
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded config from {env_path}")


class LLMConfig:
    """Configuration for LLM endpoints"""
    
    # Default to local LM Studio
    DEFAULT_ENDPOINT = "http://localhost:1234/v1/chat/completions"
    DEFAULT_MODEL = "qwen3-8b-mlx"
    
    # Dragon via Tailscale
    DRAGON_ENDPOINT = "http://100.82.232.70:1234/v1/chat/completions"
    
    # OpenRouter
    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self):
        # Get from environment or use defaults
        self.endpoint = os.getenv("LLM_ENDPOINT", self.DEFAULT_ENDPOINT)
        self.model = os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.api_key = os.getenv("OPENROUTER_API_KEY", None)
        
        # Auto-detect endpoint type
        if "openrouter" in self.endpoint:
            self.provider = "openrouter"
            if not self.api_key:
                print("⚠️  Warning: OpenRouter endpoint detected but OPENROUTER_API_KEY not set")
        elif "100.82.232.70" in self.endpoint:
            self.provider = "dragon"
            print("🐉 Using Dragon (512GB M3 Ultra) via Tailscale")
        else:
            self.provider = "lm_studio"
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for the request"""
        headers = {"Content-Type": "application/json"}
        
        if self.provider == "openrouter" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["HTTP-Referer"] = "https://github.com/LibraxisAI/lbrxVoice"
        
        return headers
    
    def get_request_params(self, 
                          messages: list,
                          temperature: float = 0.7,
                          max_tokens: int = 500,
                          stream: bool = False) -> Dict[str, Any]:
        """Get request parameters"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        # OpenRouter specific params
        if self.provider == "openrouter":
            params["top_p"] = 0.9
            params["frequency_penalty"] = 0
            params["presence_penalty"] = 0
        
        return params
    
    @classmethod
    def use_dragon(cls):
        """Quick method to switch to Dragon"""
        config = cls()
        config.endpoint = cls.DRAGON_ENDPOINT
        config.provider = "dragon"
        print("🐉 Switched to Dragon (512GB M3 Ultra)")
        return config
    
    @classmethod
    def use_local(cls):
        """Quick method to switch to local LM Studio"""
        config = cls()
        config.endpoint = cls.DEFAULT_ENDPOINT
        config.provider = "lm_studio"
        print("💻 Switched to local LM Studio")
        return config
    
    def __str__(self):
        return f"LLMConfig(provider={self.provider}, endpoint={self.endpoint}, model={self.model})"


# Global instance
llm_config = LLMConfig()


def test_config():
    """Test configuration"""
    print("🧪 Testing LLM Configuration")
    print("=" * 50)
    
    config = LLMConfig()
    print(f"Current config: {config}")
    print(f"Headers: {config.get_headers()}")
    
    # Test switching
    print("\nTesting Dragon config:")
    dragon = LLMConfig.use_dragon()
    print(f"Dragon endpoint: {dragon.endpoint}")
    
    print("\nTesting local config:")
    local = LLMConfig.use_local()
    print(f"Local endpoint: {local.endpoint}")


if __name__ == "__main__":
    test_config()