"""
Anthropic provider implementation.

Supports Claude models including Claude 3.5 Sonnet, Claude 3 Opus, and others.
"""

from typing import Optional, List
from anthropic import Anthropic, AnthropicError
from .base_provider import BaseProvider, ModelResponse, Message, MessageRole, ProviderError


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Anthropic provider.

        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022", "claude-3-opus-20240229").
            api_key: Anthropic API key.
            **kwargs: Additional parameters passed to BaseProvider.
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        self.client = Anthropic(
            api_key=api_key,
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
        """Generate response from Claude model."""
        messages = [
            {"role": "user", "content": prompt}
        ]

        return self._call_api(
            messages=messages,
            system=system_prompt,
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
        # Anthropic separates system messages from conversation
        system_prompt = None
        formatted_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        return self._call_api(
            messages=formatted_messages,
            system=system_prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs
        )

    def _call_api(
        self,
        messages: List[dict],
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> ModelResponse:
        """Internal method to call Anthropic API."""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            if system:
                params["system"] = system

            response = self.client.messages.create(**params)

            return ModelResponse(
                content=response.content[0].text,
                model=self.model,
                provider=self.get_provider_name(),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                metadata={
                    "response_id": response.id,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            )

        except AnthropicError as e:
            raise ProviderError(f"Anthropic API error: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error calling Anthropic: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"
