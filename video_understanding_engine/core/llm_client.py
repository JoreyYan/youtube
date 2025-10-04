# -*- coding: utf-8 -*-
"""LLM Client - Unified interface for OpenAI/Claude APIs"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM API client"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: str = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if not self.api_key:
            raise ValueError(f"API key not found for {provider}")

        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = model or "gpt-4o-mini"
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = model or "claude-3-haiku-20240307"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"LLMClient initialized: {self.provider}/{self.model}")

    def call(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Call LLM API"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def __repr__(self) -> str:
        return f"LLMClient(provider='{self.provider}', model='{self.model}')"
