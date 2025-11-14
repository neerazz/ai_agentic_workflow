"""
Default configurations for different use cases.

Provides pre-configured settings for common scenarios like
development, production, local testing, etc.
"""

from .orchestrator_config import (
    OrchestratorConfig,
    ModelConfig,
    ConfidenceConfig,
    ExecutionConfig,
    LoggingConfig,
    ModelProvider,
    ExecutionStrategy,
)


def get_default_config() -> OrchestratorConfig:
    """Get default production configuration."""
    return OrchestratorConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.ANTHROPIC,
            orchestrator_model="claude-3-5-sonnet-20241022",
            planner_provider=ModelProvider.OPENAI,
            planner_model="gpt-4o",
            executor_provider=ModelProvider.ANTHROPIC,
            executor_model="claude-3-5-sonnet-20241022",
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.75,
            max_clarification_rounds=3,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.GREEDY,
            fail_fast=True,
        ),
        logging=LoggingConfig(
            log_level="INFO",
            structured_logging=False,
            enable_tracing=True,
        ),
    )


def get_development_config() -> OrchestratorConfig:
    """Get configuration optimized for development."""
    return OrchestratorConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.ANTHROPIC,
            orchestrator_model="claude-3-5-sonnet-20241022",
            planner_provider=ModelProvider.ANTHROPIC,
            planner_model="claude-3-5-sonnet-20241022",
            executor_provider=ModelProvider.ANTHROPIC,
            executor_model="claude-3-5-sonnet-20241022",
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.70,
            max_clarification_rounds=2,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.GREEDY,
            fail_fast=False,  # Continue on errors for debugging
        ),
        logging=LoggingConfig(
            log_level="DEBUG",
            structured_logging=True,
            enable_tracing=True,
            log_model_calls=True,
            log_prompts=True,
            export_traces=True,
        ),
    )


def get_local_lmstudio_config() -> OrchestratorConfig:
    """Get configuration for local LM Studio testing."""
    return OrchestratorConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.LMSTUDIO,
            orchestrator_model="local-model",
            planner_provider=ModelProvider.LMSTUDIO,
            planner_model="local-model",
            executor_provider=ModelProvider.LMSTUDIO,
            executor_model="local-model",
            orchestrator_temperature=0.7,
            planner_temperature=0.3,
            executor_temperature=0.5,
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.70,
            max_clarification_rounds=2,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.SEQUENTIAL,
            task_timeout=600,  # Local models may be slower
        ),
        logging=LoggingConfig(
            log_level="INFO",
            structured_logging=False,
            enable_tracing=True,
            log_model_calls=True,
        ),
    )


def get_fast_config() -> OrchestratorConfig:
    """Get configuration optimized for speed (using faster models)."""
    return OrchestratorConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.OPENAI,
            orchestrator_model="gpt-4o-mini",
            planner_provider=ModelProvider.OPENAI,
            planner_model="gpt-4o-mini",
            executor_provider=ModelProvider.GROQ,
            executor_model="llama-3.1-70b-versatile",
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.70,
            max_clarification_rounds=2,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.PARALLEL,
            max_parallel_tasks=10,
        ),
        logging=LoggingConfig(
            log_level="INFO",
            structured_logging=False,
            enable_tracing=False,  # Disable for speed
        ),
    )


def get_high_accuracy_config() -> OrchestratorConfig:
    """Get configuration optimized for accuracy over speed."""
    return OrchestratorConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.ANTHROPIC,
            orchestrator_model="claude-3-opus-20240229",
            planner_provider=ModelProvider.OPENAI,
            planner_model="gpt-4",
            executor_provider=ModelProvider.ANTHROPIC,
            executor_model="claude-3-opus-20240229",
            orchestrator_temperature=0.3,
            planner_temperature=0.1,
            executor_temperature=0.2,
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.85,
            max_clarification_rounds=5,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.GREEDY,
            max_retries=5,
            validate_results=True,
            fail_fast=True,
        ),
        logging=LoggingConfig(
            log_level="DEBUG",
            structured_logging=True,
            enable_tracing=True,
            log_model_calls=True,
            log_prompts=True,
            export_traces=True,
        ),
    )


def get_config_by_name(name: str) -> OrchestratorConfig:
    """
    Get configuration by name.

    Args:
        name: Configuration name. One of:
            - "default": Standard production config
            - "development": Development with debug logging
            - "local": LM Studio local testing
            - "fast": Optimized for speed
            - "accurate": Optimized for accuracy

    Returns:
        OrchestratorConfig instance.

    Raises:
        ValueError: If config name is not recognized.
    """
    configs = {
        "default": get_default_config,
        "development": get_development_config,
        "local": get_local_lmstudio_config,
        "fast": get_fast_config,
        "accurate": get_high_accuracy_config,
    }

    if name not in configs:
        raise ValueError(
            f"Unknown config name: {name}. "
            f"Available configs: {', '.join(configs.keys())}"
        )

    return configs[name]()
