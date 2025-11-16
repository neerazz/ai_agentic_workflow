"""
Model-agnostic LLM interface for orchestrator system.

Provides unified interface for multiple AI providers including
OpenAI, Anthropic, Google, Groq, DeepSeek, LM Studio, and more.
"""

from .model_manager import ModelManager, ModelResponse
from .providers.base_provider import BaseProvider, ProviderError

__all__ = [
    'ModelManager',
    'ModelResponse',
    'BaseProvider',
    'ProviderError',
]
