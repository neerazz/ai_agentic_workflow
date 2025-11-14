"""
LM Studio provider implementation.

Supports local models running via LM Studio's OpenAI-compatible API.
Also compatible with other local inference servers like Ollama, vLLM, etc.
"""

from typing import Optional, List
from openai import OpenAI, OpenAIError
from .base_provider import BaseProvider, ModelResponse, Message, ProviderError


class LMStudioProvider(BaseProvider):
    """Provider for LM Studio local models."""

    def __init__(
        self,
        model: str = "local-model",
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "not-needed",  # LM Studio doesn't require API key
        **kwargs
    ):
        """
        Initialize LM Studio provider.

        Args:
            model: Model identifier in LM Studio.
            base_url: Base URL for LM Studio server (default: http://localhost:1234/v1).
            api_key: API key (not needed for LM Studio, but required by OpenAI client).
            **kwargs: Additional parameters passed to BaseProvider.
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        self.base_url = base_url
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.timeout,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate response from local model."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self._call_api(
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs
        )

    def generate_with_history(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate response with conversation history."""
        formatted_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        return self._call_api(
            messages=formatted_messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs
        )

    def _call_api(
        self,
        messages: List[dict],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> ModelResponse:
        """Internal method to call LM Studio API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            # Handle case where usage might not be provided by local models
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens

            return ModelResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider=self.get_provider_name(),
                tokens_used=tokens_used,
                finish_reason=response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else None,
                metadata={
                    "base_url": self.base_url,
                    "response_id": getattr(response, 'id', None),
                }
            )

        except OpenAIError as e:
            raise ProviderError(f"LM Studio API error: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error calling LM Studio: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "lmstudio"

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        # LM Studio doesn't require API key validation
        if not self.model:
            raise ProviderError("Model name is required")

        if not self.base_url:
            raise ProviderError("Base URL is required for LM Studio")

        return super().validate_config()
