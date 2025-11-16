"""
Decision Maker for intelligent retry and proceed logic.

Analyzes critique results and execution history to make informed
decisions about task retries, improvements, and workflow progression.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .critique_engine import CritiqueResult, CritiqueDecision
from ..logging import get_logger, trace_context
from ..llm.model_manager import ModelManager


class DecisionReason(str, Enum):
    """Reasons for decision outcomes."""
    QUALITY_ACCEPTABLE = "quality_acceptable"
    QUALITY_IMPROVED = "quality_improved"
    MAX_RETRIES_REACHED = "max_retries_reached"
    CRITICAL_ISSUES = "critical_issues"
    NO_IMPROVEMENT = "no_improvement"
    MINOR_ISSUES_ONLY = "minor_issues_only"


@dataclass
class Decision:
    """
    Decision outcome with reasoning.
    """
    # Should we proceed or retry?
    should_proceed: bool

    # Should we retry this specific task?
    should_retry_task: bool

    # Reason for the decision
    reason: DecisionReason

    # Explanation
    explanation: str

    # Suggested improvements if retrying
    improvements: List[str] = field(default_factory=list)

    # Confidence in decision (0.0 - 1.0)
    confidence: float = 0.8

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'should_proceed': self.should_proceed,
            'should_retry_task': self.should_retry_task,
            'reason': self.reason.value,
            'explanation': self.explanation,
            'improvements': self.improvements,
            'confidence': self.confidence,
            'metadata': self.metadata,
        }


class DecisionMaker:
    """
    Intelligent decision maker for task retry and progression logic.

    Analyzes critique results, execution history, and quality trends
    to make informed decisions about retries and improvements.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        max_retries: int = 3,
        quality_threshold: float = 0.75,
        improvement_threshold: float = 0.10
    ):
        """
        Initialize decision maker.

        Args:
            model_manager: Model manager for AI-assisted decisions.
            max_retries: Maximum retry attempts per task.
            quality_threshold: Minimum acceptable quality score.
            improvement_threshold: Minimum improvement needed to continue retrying.
        """
        self.model_manager = model_manager
        self.max_retries = max_retries
        self.quality_threshold = quality_threshold
        self.improvement_threshold = improvement_threshold
        self.logger = get_logger(__name__)

        self.logger.info("DecisionMaker initialized", metadata={
            "max_retries": max_retries,
            "quality_threshold": quality_threshold,
            "improvement_threshold": improvement_threshold,
        })

    def decide_on_task(
        self,
        critique: CritiqueResult,
        attempt_number: int,
        previous_critiques: Optional[List[CritiqueResult]] = None
    ) -> Decision:
        """
        Decide whether to proceed or retry a task based on critique.

        Args:
            critique: Latest critique result.
            attempt_number: Current attempt number (1-indexed).
            previous_critiques: List of previous critique results.

        Returns:
            Decision with reasoning and improvements.
        """
        with trace_context("decide_on_task") as span_id:
            self.logger.info(f"Making decision for attempt {attempt_number}", metadata={
                "quality_score": critique.quality_score,
                "decision": critique.decision.value,
                "critical_issues": len(critique.critical_issues),
            })

            # Rule 1: Accept if critique says ACCEPT and quality meets threshold
            if critique.decision == CritiqueDecision.ACCEPT and critique.quality_score >= self.quality_threshold:
                return Decision(
                    should_proceed=True,
                    should_retry_task=False,
                    reason=DecisionReason.QUALITY_ACCEPTABLE,
                    explanation=f"Quality score {critique.quality_score:.2f} meets threshold {self.quality_threshold:.2f}. Output is acceptable.",
                    confidence=0.9,
                )

            # Rule 2: Max retries reached - must proceed
            if attempt_number >= self.max_retries:
                return Decision(
                    should_proceed=True,
                    should_retry_task=False,
                    reason=DecisionReason.MAX_RETRIES_REACHED,
                    explanation=f"Maximum retries ({self.max_retries}) reached. Proceeding with best available output.",
                    confidence=0.7,
                    metadata={'warning': 'Quality may be suboptimal'}
                )

            # Rule 3: Critical issues present - must retry
            if critique.critical_issues:
                return Decision(
                    should_proceed=False,
                    should_retry_task=True,
                    reason=DecisionReason.CRITICAL_ISSUES,
                    explanation=f"Found {len(critique.critical_issues)} critical issue(s) that must be fixed.",
                    improvements=critique.suggestions,
                    confidence=0.95,
                )

            # Rule 4: Check if we're improving
            if previous_critiques:
                is_improving = self._is_improving(critique, previous_critiques)

                if not is_improving:
                    # Not improving - stop retrying
                    return Decision(
                        should_proceed=True,
                        should_retry_task=False,
                        reason=DecisionReason.NO_IMPROVEMENT,
                        explanation="Quality is not improving with retries. Proceeding with current output.",
                        confidence=0.8,
                    )
                else:
                    # Improving - continue retrying
                    return Decision(
                        should_proceed=False,
                        should_retry_task=True,
                        reason=DecisionReason.QUALITY_IMPROVED,
                        explanation=f"Quality improving. Score: {critique.quality_score:.2f}. Retry recommended.",
                        improvements=critique.suggestions,
                        confidence=0.85,
                    )

            # Rule 5: Minor issues only - accept if close to threshold
            if not critique.critical_issues and critique.quality_score >= (self.quality_threshold - 0.10):
                return Decision(
                    should_proceed=True,
                    should_retry_task=False,
                    reason=DecisionReason.MINOR_ISSUES_ONLY,
                    explanation=f"Only minor issues found. Quality {critique.quality_score:.2f} is close enough to threshold.",
                    confidence=0.75,
                )

            # Default: Retry with improvements
            return Decision(
                should_proceed=False,
                should_retry_task=True,
                reason=DecisionReason.CRITICAL_ISSUES,
                explanation=f"Quality {critique.quality_score:.2f} below threshold. Retry with improvements.",
                improvements=critique.suggestions,
                confidence=0.8,
            )

    def decide_on_workflow(
        self,
        task_decisions: List[Decision],
        overall_critique: Optional[CritiqueResult] = None
    ) -> Decision:
        """
        Decide on overall workflow progression.

        Args:
            task_decisions: List of decisions for individual tasks.
            overall_critique: Optional overall workflow critique.

        Returns:
            Decision for workflow continuation.
        """
        with trace_context("decide_on_workflow") as span_id:
            self.logger.info("Making workflow decision", metadata={
                "task_count": len(task_decisions),
            })

            # Check if all tasks succeeded
            all_succeeded = all(d.should_proceed for d in task_decisions)

            if all_succeeded:
                if overall_critique and overall_critique.decision == CritiqueDecision.ACCEPT:
                    return Decision(
                        should_proceed=True,
                        should_retry_task=False,
                        reason=DecisionReason.QUALITY_ACCEPTABLE,
                        explanation="All tasks completed successfully with acceptable quality.",
                        confidence=0.95,
                    )

            # Check for critical failures
            critical_failures = sum(
                1 for d in task_decisions
                if d.reason == DecisionReason.MAX_RETRIES_REACHED
            )

            if critical_failures > 0:
                return Decision(
                    should_proceed=True,
                    should_retry_task=False,
                    reason=DecisionReason.MAX_RETRIES_REACHED,
                    explanation=f"{critical_failures} task(s) reached max retries. Proceeding with available outputs.",
                    confidence=0.6,
                    metadata={'warning': 'Some tasks may have suboptimal quality'}
                )

            # Default: proceed with current state
            return Decision(
                should_proceed=True,
                should_retry_task=False,
                reason=DecisionReason.QUALITY_ACCEPTABLE,
                explanation="Workflow completed with acceptable results.",
                confidence=0.8,
            )

    def _is_improving(
        self,
        current: CritiqueResult,
        previous: List[CritiqueResult]
    ) -> bool:
        """
        Check if quality is improving over attempts.

        Args:
            current: Current critique result.
            previous: Previous critique results.

        Returns:
            True if improving, False otherwise.
        """
        if not previous:
            return True

        # Get last critique
        last = previous[-1]

        # Check if quality improved
        improvement = current.quality_score - last.quality_score

        if improvement >= self.improvement_threshold:
            self.logger.info(f"Quality improved by {improvement:.2f}")
            return True

        # Check if critical issues reduced
        if len(current.critical_issues) < len(last.critical_issues):
            self.logger.info("Critical issues reduced")
            return True

        self.logger.info(f"No significant improvement. Delta: {improvement:.2f}")
        return False

    def analyze_trends(
        self,
        critique_history: List[CritiqueResult]
    ) -> Dict[str, Any]:
        """
        Analyze quality trends over multiple attempts.

        Args:
            critique_history: List of critique results over time.

        Returns:
            Dictionary with trend analysis.
        """
        if not critique_history:
            return {
                'trend': 'unknown',
                'average_quality': 0.0,
                'improvement_rate': 0.0,
            }

        scores = [c.quality_score for c in critique_history]

        # Calculate metrics
        average = sum(scores) / len(scores)
        trend = 'improving' if scores[-1] > scores[0] else 'declining' if scores[-1] < scores[0] else 'stable'
        improvement_rate = (scores[-1] - scores[0]) / len(scores) if len(scores) > 1 else 0.0

        return {
            'trend': trend,
            'average_quality': average,
            'improvement_rate': improvement_rate,
            'best_score': max(scores),
            'worst_score': min(scores),
            'attempts': len(scores),
        }
