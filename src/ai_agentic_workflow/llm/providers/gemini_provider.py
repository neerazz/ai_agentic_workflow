"""
Google Gemini provider implementation.

Supports Gemini models with generous free tier (1,500 requests/day).
Great for reasoning and task planning.
"""

from typing import Optional, List
import google.generativeai as genai
from .base_provider import BaseProvider, ModelResponse, Message, MessageRole, ProviderError


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models."""

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini provider.

        Args:
            model: Model name (e.g., "gemini-1.5-pro", "gemini-1.5-flash").
            api_key: Google API key.
            **kwargs: Additional parameters passed to BaseProvider.
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Create model instance
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }

        self.client = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate response from Gemini model."""
        # Combine system prompt with user prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        return self._call_api(
            prompt=full_prompt,
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
        # Convert messages to Gemini format
        history = []
        system_instruction = None

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            elif msg.role == MessageRole.USER:
                history.append({
                    "role": "user",
                    "parts": [msg.content]
                })
            elif msg.role == MessageRole.ASSISTANT:
                history.append({
                    "role": "model",
                    "parts": [msg.content]
                })

        # Start chat with history
        chat = self.client.start_chat(history=history[:-1] if history else [])

        # Get last user message
        last_message = history[-1]["parts"][0] if history else ""

        # Add system instruction if present
        if system_instruction:
            last_message = f"{system_instruction}\n\n{last_message}"

        return self._call_api(
            prompt=last_message,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            chat=chat,
            **kwargs
        )

    def _call_api(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        chat=None,
        **kwargs
    ) -> ModelResponse:
        """Internal method to call Gemini API."""
        try:
            # Update generation config if different from default
            if temperature != self.temperature or max_tokens != self.max_tokens:
                generation_config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                # Create new model instance with updated config
                model = genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=generation_config
                )
            else:
                model = self.client

            # Generate response
            if chat:
                response = chat.send_message(prompt)
            else:
                response = model.generate_content(prompt)

            # Extract text from response
            content = response.text

            # Get token count if available
            tokens_used = None
            if hasattr(response, 'usage_metadata'):
                tokens_used = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )

            return ModelResponse(
                content=content,
                model=self.model,
                provider=self.get_provider_name(),
                tokens_used=tokens_used,
                finish_reason=None,  # Gemini doesn't provide finish_reason in the same way
                metadata={
                    "safety_ratings": getattr(response, 'safety_ratings', None),
                }
            )

        except Exception as e:
            raise ProviderError(f"Gemini API error: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "google"

    def validate_config(self) -> bool:
        """Validate provider configuration."""
        if not self.api_key:
            raise ProviderError("Google API key is required for Gemini provider")

        return super().validate_config()
