"""
Model manager for unified interaction with multiple AI providers.

Provides a single interface to interact with different AI models,
handles provider selection, configuration, and failover.
"""

from typing import Optional, Dict, Any, List
from ..config.orchestrator_config import ModelConfig, ModelProvider
from ..logging import get_logger, trace_context
from .providers.base_provider import (
    BaseProvider,
    ModelResponse,
    Message,
    MessageRole,
    ProviderError
)
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.lmstudio_provider import LMStudioProvider
from .providers.groq_provider import GroqProvider
from .providers.gemini_provider import GeminiProvider


class ModelManagerError(Exception):
    """Exception raised by ModelManager."""
    pass


class ModelManager:
    """
    Manages AI model providers and provides unified interface.

    Handles provider instantiation, configuration, and provides
    consistent API for model interactions regardless of provider.
    """

    def __init__(self, config: ModelConfig):
        """
        Initialize model manager with configuration.

        Args:
            config: ModelConfig with provider settings and API keys.
        """
        self.config = config
        self.logger = get_logger(__name__)
        self._providers: Dict[str, BaseProvider] = {}

        # Validate configuration
        errors = config.validate()
        if errors:
            error_msg = "Model configuration validation failed:\n" + "\n".join(errors)
            self.logger.error(error_msg)
            raise ModelManagerError(error_msg)

        self.logger.info("ModelManager initialized with config", metadata={
            "orchestrator": f"{config.orchestrator_provider.value}/{config.orchestrator_model}",
            "planner": f"{config.planner_provider.value}/{config.planner_model}",
            "executor": f"{config.executor_provider.value}/{config.executor_model}",
        })

    def _get_provider(self, provider_type: str, provider_name: ModelProvider, model: str, temperature: float) -> BaseProvider:
        """
        Get or create provider instance.

        Args:
            provider_type: Type identifier (e.g., "orchestrator", "planner").
            provider_name: ModelProvider enum value.
            model: Model name.
            temperature: Sampling temperature.

        Returns:
            BaseProvider instance.

        Raises:
            ModelManagerError: If provider cannot be created.
        """
        cache_key = f"{provider_type}_{provider_name.value}_{model}"

        # Return cached provider if exists
        if cache_key in self._providers:
            return self._providers[cache_key]

        # Create new provider
        try:
            if provider_name == ModelProvider.OPENAI:
                provider = OpenAIProvider(
                    model=model,
                    api_key=self.config.openai_api_key,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.ANTHROPIC:
                provider = AnthropicProvider(
                    model=model,
                    api_key=self.config.anthropic_api_key,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.LMSTUDIO:
                provider = LMStudioProvider(
                    model=model,
                    base_url=self.config.lmstudio_base_url,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.GOOGLE:
                provider = GeminiProvider(
                    model=model,
                    api_key=self.config.google_api_key,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.GROQ:
                provider = GroqProvider(
                    model=model,
                    api_key=self.config.groq_api_key,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.DEEPSEEK:
                # DeepSeek uses OpenAI-compatible API
                provider = OpenAIProvider(
                    model=model,
                    api_key=self.config.deepseek_api_key,
                    base_url="https://api.deepseek.com/v1",
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            elif provider_name == ModelProvider.PERPLEXITY:
                # Perplexity uses OpenAI-compatible API
                provider = OpenAIProvider(
                    model=model,
                    api_key=self.config.perplexity_api_key,
                    base_url="https://api.perplexity.ai",
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            else:
                raise ModelManagerError(f"Unsupported provider: {provider_name.value}")

            # Validate provider configuration
            provider.validate_config()

            # Cache provider
            self._providers[cache_key] = provider

            self.logger.info(f"Created {provider_type} provider", metadata={
                "provider": provider_name.value,
                "model": model,
                "temperature": temperature,
            })

            return provider

        except Exception as e:
            self.logger.error(f"Failed to create {provider_type} provider", metadata={
                "provider": provider_name.value,
                "error": str(e),
            }, exc_info=True)
            raise ModelManagerError(f"Failed to create provider {provider_name.value}: {str(e)}") from e

    def orchestrator_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response using orchestrator model.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse from orchestrator model.
        """
        with trace_context("orchestrator_generate") as span_id:
            self.logger.info("Orchestrator generating response", metadata={
                "prompt_length": len(prompt),
                "has_system_prompt": system_prompt is not None,
            })

            provider = self._get_provider(
                "orchestrator",
                self.config.orchestrator_provider,
                self.config.orchestrator_model,
                self.config.orchestrator_temperature,
            )

            try:
                response = provider.generate(prompt, system_prompt, **kwargs)

                self.logger.info("Orchestrator response generated", metadata={
                    "response_length": len(response.content),
                    "tokens_used": response.tokens_used,
                    "model": response.model,
                })

                return response

            except ProviderError as e:
                self.logger.error("Orchestrator generation failed", metadata={
                    "error": str(e),
                }, exc_info=True)
                raise ModelManagerError(f"Orchestrator generation failed: {str(e)}") from e

    def planner_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response using planner model.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse from planner model.
        """
        with trace_context("planner_generate") as span_id:
            self.logger.info("Planner generating response", metadata={
                "prompt_length": len(prompt),
            })

            provider = self._get_provider(
                "planner",
                self.config.planner_provider,
                self.config.planner_model,
                self.config.planner_temperature,
            )

            try:
                response = provider.generate(prompt, system_prompt, **kwargs)

                self.logger.info("Planner response generated", metadata={
                    "response_length": len(response.content),
                    "tokens_used": response.tokens_used,
                })

                return response

            except ProviderError as e:
                self.logger.error("Planner generation failed", metadata={
                    "error": str(e),
                }, exc_info=True)
                raise ModelManagerError(f"Planner generation failed: {str(e)}") from e

    def executor_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response using executor model.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse from executor model.
        """
        with trace_context("executor_generate") as span_id:
            self.logger.info("Executor generating response", metadata={
                "prompt_length": len(prompt),
            })

            provider = self._get_provider(
                "executor",
                self.config.executor_provider,
                self.config.executor_model,
                self.config.executor_temperature,
            )

            try:
                response = provider.generate(prompt, system_prompt, **kwargs)

                self.logger.info("Executor response generated", metadata={
                    "response_length": len(response.content),
                    "tokens_used": response.tokens_used,
                })

                return response

            except ProviderError as e:
                self.logger.error("Executor generation failed", metadata={
                    "error": str(e),
                }, exc_info=True)
                raise ModelManagerError(f"Executor generation failed: {str(e)}") from e

    def generate_with_provider(
        self,
        provider_name: ModelProvider,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate response with specific provider and model.

        Args:
            provider_name: Provider to use.
            model: Model name.
            prompt: User prompt.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse from specified provider.
        """
        with trace_context("custom_generate") as span_id:
            provider = self._get_provider(
                "custom",
                provider_name,
                model,
                temperature,
            )

            return provider.generate(prompt, system_prompt, **kwargs)
