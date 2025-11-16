"""
Configuration classes for orchestrator system.

Provides type-safe, validated configuration for all components
of the agentic workflow orchestrator.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    LMSTUDIO = "lmstudio"
    PERPLEXITY = "perplexity"


class ExecutionStrategy(str, Enum):
    """Task execution strategies."""
    GREEDY = "greedy"  # Execute each task optimally
    PARALLEL = "parallel"  # Execute independent tasks in parallel
    SEQUENTIAL = "sequential"  # Execute tasks one by one


@dataclass
class ModelConfig:
    """Configuration for AI model providers."""

    # Primary orchestrator model
    orchestrator_provider: ModelProvider = ModelProvider.ANTHROPIC
    orchestrator_model: str = "claude-3-5-sonnet-20241022"
    orchestrator_temperature: float = 0.7

    # Task planner model
    planner_provider: ModelProvider = ModelProvider.OPENAI
    planner_model: str = "gpt-4o"
    planner_temperature: float = 0.3

    # Task executor model
    executor_provider: ModelProvider = ModelProvider.ANTHROPIC
    executor_model: str = "claude-3-5-sonnet-20241022"
    executor_temperature: float = 0.5

    # API keys (loaded from environment)
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    groq_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    deepseek_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))
    perplexity_api_key: Optional[str] = field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY"))

    # LM Studio configuration
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = "local-model"

    # Model-specific settings
    max_tokens: int = 4096
    timeout: int = 60  # seconds

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Check that required API keys are present for configured providers
        provider_key_map = {
            ModelProvider.OPENAI: self.openai_api_key,
            ModelProvider.ANTHROPIC: self.anthropic_api_key,
            ModelProvider.GOOGLE: self.google_api_key,
            ModelProvider.GROQ: self.groq_api_key,
            ModelProvider.DEEPSEEK: self.deepseek_api_key,
            ModelProvider.PERPLEXITY: self.perplexity_api_key,
        }

        for provider in [self.orchestrator_provider, self.planner_provider, self.executor_provider]:
            if provider in provider_key_map and not provider_key_map[provider]:
                errors.append(f"Missing API key for provider: {provider.value}")

        # Validate temperature ranges
        for temp_name, temp_value in [
            ("orchestrator_temperature", self.orchestrator_temperature),
            ("planner_temperature", self.planner_temperature),
            ("executor_temperature", self.executor_temperature),
        ]:
            if not 0.0 <= temp_value <= 2.0:
                errors.append(f"{temp_name} must be between 0.0 and 2.0, got {temp_value}")

        # Validate positive integers
        if self.max_tokens <= 0:
            errors.append(f"max_tokens must be positive, got {self.max_tokens}")
        if self.timeout <= 0:
            errors.append(f"timeout must be positive, got {self.timeout}")

        return errors


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring system."""

    # Confidence threshold (0.0 - 1.0)
    min_confidence_threshold: float = 0.75

    # Weights for different confidence factors (should sum to 1.0)
    clarity_weight: float = 0.30
    completeness_weight: float = 0.30
    feasibility_weight: float = 0.25
    specificity_weight: float = 0.15

    # Maximum number of clarification rounds
    max_clarification_rounds: int = 3

    # Enable/disable automatic clarification
    auto_clarify: bool = True

    def validate(self) -> List[str]:
        """Validate confidence configuration."""
        errors = []

        # Check threshold range
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            errors.append(
                f"min_confidence_threshold must be between 0.0 and 1.0, got {self.min_confidence_threshold}"
            )

        # Check weights sum to 1.0 (with small tolerance for floating point)
        total_weight = (
            self.clarity_weight +
            self.completeness_weight +
            self.feasibility_weight +
            self.specificity_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Confidence weights must sum to 1.0, got {total_weight}")

        # Check individual weight ranges
        for weight_name, weight_value in [
            ("clarity_weight", self.clarity_weight),
            ("completeness_weight", self.completeness_weight),
            ("feasibility_weight", self.feasibility_weight),
            ("specificity_weight", self.specificity_weight),
        ]:
            if not 0.0 <= weight_value <= 1.0:
                errors.append(f"{weight_name} must be between 0.0 and 1.0, got {weight_value}")

        # Check max rounds
        if self.max_clarification_rounds < 1:
            errors.append(
                f"max_clarification_rounds must be at least 1, got {self.max_clarification_rounds}"
            )

        return errors


@dataclass
class ExecutionConfig:
    """Configuration for task execution."""

    # Execution strategy
    strategy: ExecutionStrategy = ExecutionStrategy.GREEDY

    # Maximum number of retries for failed tasks
    max_retries: int = 3

    # Retry backoff (seconds)
    retry_backoff: float = 1.0

    # Maximum number of parallel tasks (for parallel strategy)
    max_parallel_tasks: int = 5

    # Task timeout (seconds)
    task_timeout: int = 300

    # Enable task result validation
    validate_results: bool = True

    # Fail-fast mode: stop on first error
    fail_fast: bool = True

    def validate(self) -> List[str]:
        """Validate execution configuration."""
        errors = []

        if self.max_retries < 0:
            errors.append(f"max_retries must be non-negative, got {self.max_retries}")

        if self.retry_backoff < 0:
            errors.append(f"retry_backoff must be non-negative, got {self.retry_backoff}")

        if self.max_parallel_tasks < 1:
            errors.append(f"max_parallel_tasks must be at least 1, got {self.max_parallel_tasks}")

        if self.task_timeout <= 0:
            errors.append(f"task_timeout must be positive, got {self.task_timeout}")

        return errors


@dataclass
class LoggingConfig:
    """Configuration for logging and tracing."""

    # Logging level
    log_level: str = "INFO"

    # Enable structured JSON logging
    structured_logging: bool = False

    # Enable distributed tracing
    enable_tracing: bool = True

    # Log model interactions
    log_model_calls: bool = True

    # Log prompts and responses (can be verbose)
    log_prompts: bool = False

    # Export traces to file
    export_traces: bool = False
    trace_export_path: str = "./traces"

    def validate(self) -> List[str]:
        """Validate logging configuration."""
        errors = []

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(f"log_level must be one of {valid_levels}, got {self.log_level}")

        if self.export_traces:
            # Check if path is valid (basic check)
            if not self.trace_export_path:
                errors.append("trace_export_path must be provided when export_traces is True")

        return errors


@dataclass
class OrchestratorConfig:
    """Main configuration for the orchestrator system."""

    model: ModelConfig = field(default_factory=ModelConfig)
    confidence: ConfidenceConfig = field(default_factory=ConfidenceConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """
        Validate entire configuration.

        Returns:
            List of all validation errors across all config sections.
        """
        errors = []
        errors.extend(self.model.validate())
        errors.extend(self.confidence.validate())
        errors.extend(self.execution.validate())
        errors.extend(self.logging.validate())
        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_validation_report(self) -> str:
        """Get a formatted validation report."""
        errors = self.validate()
        if not errors:
            return "✓ Configuration is valid"

        report = "✗ Configuration validation failed:\n"
        for i, error in enumerate(errors, 1):
            report += f"  {i}. {error}\n"
        return report

    @classmethod
    def from_env(cls) -> 'OrchestratorConfig':
        """
        Create configuration from environment variables.

        Looks for environment variables with specific prefixes:
        - MODEL_*
        - CONFIDENCE_*
        - EXECUTION_*
        - LOGGING_*
        """
        config = cls()

        # Override with environment variables if present
        # Model config
        if orchestrator_provider := os.getenv("MODEL_ORCHESTRATOR_PROVIDER"):
            config.model.orchestrator_provider = ModelProvider(orchestrator_provider)
        if orchestrator_model := os.getenv("MODEL_ORCHESTRATOR_MODEL"):
            config.model.orchestrator_model = orchestrator_model

        # Confidence config
        if min_conf := os.getenv("CONFIDENCE_MIN_THRESHOLD"):
            config.confidence.min_confidence_threshold = float(min_conf)

        # Execution config
        if strategy := os.getenv("EXECUTION_STRATEGY"):
            config.execution.strategy = ExecutionStrategy(strategy)

        # Logging config
        if log_level := os.getenv("LOG_LEVEL"):
            config.logging.log_level = log_level
        if structured := os.getenv("STRUCTURED_LOGGING"):
            config.logging.structured_logging = structured.lower() == "true"

        return config
