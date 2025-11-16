"""
OpenAI provider implementation.

Supports OpenAI models including GPT-4, GPT-4o, GPT-3.5, and compatible APIs.
"""

from typing import Optional, List
from openai import OpenAI, OpenAIError
from .base_provider import BaseProvider, ModelResponse, Message, ProviderError


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI provider.

        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4", "gpt-3.5-turbo").
            api_key: OpenAI API key.
            base_url: Optional custom base URL for API.
            organization: Optional organization ID.
            **kwargs: Additional parameters passed to BaseProvider.
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
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
        """Generate response from OpenAI model."""
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
        """Internal method to call OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return ModelResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider=self.get_provider_name(),
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "response_id": response.id,
                    "created": response.created,
                }
            )

        except OpenAIError as e:
            raise ProviderError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error calling OpenAI: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"
