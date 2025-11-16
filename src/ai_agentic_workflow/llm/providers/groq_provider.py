"""
Groq provider implementation.

Supports Groq's ultra-fast inference with generous free tier.
Great for critique and evaluation tasks.
"""

from typing import Optional, List
from openai import OpenAI, OpenAIError
from .base_provider import BaseProvider, ModelResponse, Message, ProviderError


class GroqProvider(BaseProvider):
    """Provider for Groq's fast inference models."""

    def __init__(
        self,
        model: str = "llama-3.1-70b-versatile",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Groq provider.

        Args:
            model: Model name (e.g., "llama-3.1-70b-versatile", "mixtral-8x7b-32768").
            api_key: Groq API key.
            **kwargs: Additional parameters passed to BaseProvider.
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
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
        """Generate response from Groq model."""
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
        """Internal method to call Groq API."""
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
            raise ProviderError(f"Groq API error: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error calling Groq: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "groq"
