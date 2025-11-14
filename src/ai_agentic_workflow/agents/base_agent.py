"""
Base Agent abstract class for creating extensible agents.

Provides template pattern for building custom agents with
consistent interface and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from dataclasses import dataclass

from ..config import OrchestratorConfig
from ..llm.model_manager import ModelManager
from ..logging import get_logger


@dataclass
class AgentResult:
    """Standard result from agent execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Provides common infrastructure and defines the agent lifecycle.
    Custom agents should inherit from this class.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        name: Optional[str] = None
    ):
        """
        Initialize base agent.

        Args:
            config: Orchestrator configuration.
            name: Agent name (defaults to class name).
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.model_manager = ModelManager(config.model)
        self.logger = get_logger(f"{__name__}.{self.name}")

        self.logger.info(f"{self.name} initialized")

    @abstractmethod
    def execute(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute the agent's main workflow.

        Args:
            user_input: User's input/request.
            context: Optional execution context.

        Returns:
            AgentResult with execution outcome.
        """
        pass

    def validate_input(self, user_input: str) -> bool:
        """
        Validate user input before execution.

        Args:
            user_input: User's input to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not user_input or not user_input.strip():
            self.logger.error("Empty user input")
            return False
        return True

    def handle_error(self, error: Exception) -> AgentResult:
        """
        Handle errors during execution.

        Args:
            error: Exception that occurred.

        Returns:
            AgentResult with error information.
        """
        self.logger.error(f"Agent execution failed: {error}", exc_info=True)

        return AgentResult(
            success=False,
            output=None,
            error=str(error),
            metadata={'exception_type': type(error).__name__}
        )

    def __repr__(self) -> str:
        return f"{self.name}(config={self.config})"
