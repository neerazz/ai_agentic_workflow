"""
Base provider interface for AI model interactions.

Defines the contract that all provider implementations must follow
for consistent, model-agnostic interactions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    pass


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: MessageRole
    content: str


@dataclass
class ModelResponse:
    """Standardized response from any model provider."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseProvider(ABC):
    """
    Abstract base class for AI model providers.

    All provider implementations must inherit from this class and
    implement the required methods for consistent interaction.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize provider.

        Args:
            model: Model identifier.
            api_key: API key for authentication.
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Maximum tokens in response.
            timeout: Request timeout in seconds.
            **kwargs: Additional provider-specific parameters.
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_params = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate a response from the model.

        Args:
            prompt: User prompt/message.
            system_prompt: Optional system prompt for context.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ModelResponse with the generated content.

        Raises:
            ProviderError: If generation fails.
        """
        pass

    @abstractmethod
    def generate_with_history(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response with conversation history.

        Args:
            messages: List of previous messages in conversation.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ModelResponse with the generated content.

        Raises:
            ProviderError: If generation fails.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.

        Returns:
            Provider name (e.g., "openai", "anthropic").
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if configuration is valid.

        Raises:
            ProviderError: If configuration is invalid.
        """
        if not self.model:
            raise ProviderError("Model name is required")

        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ProviderError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")

        if self.max_tokens <= 0:
            raise ProviderError(f"max_tokens must be positive, got {self.max_tokens}")

        if self.timeout <= 0:
            raise ProviderError(f"timeout must be positive, got {self.timeout}")

        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model}, temperature={self.temperature})"
