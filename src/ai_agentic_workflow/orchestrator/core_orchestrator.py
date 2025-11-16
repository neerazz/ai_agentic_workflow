"""
Core orchestrator integrating all workflow components.

Main entry point for agentic workflow execution with confidence
scoring, clarification, planning, and greedy execution.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import OrchestratorConfig
from ..logging import get_logger, trace_context, get_trace_manager
from ..llm.model_manager import ModelManager

from .confidence_scorer import ConfidenceScorer, ConfidenceScore
from .clarification_handler import ClarificationHandler
from .task_planner import TaskPlanner, TaskPlan
from .task_executor import TaskExecutor, ExecutionResult


@dataclass
class OrchestratorResult:
    """Complete result from orchestrator execution."""

    # User request
    original_query: str
    enhanced_query: Optional[str] = None

    # Confidence assessment
    confidence_score: Optional[ConfidenceScore] = None
    clarification_rounds: int = 0

    # Task planning
    task_plan: Optional[TaskPlan] = None

    # Execution results
    execution_results: Dict[str, ExecutionResult] = field(default_factory=dict)

    # Final output
    final_output: Optional[str] = None

    # Metadata
    success: bool = False
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    trace_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'original_query': self.original_query,
            'enhanced_query': self.enhanced_query,
            'confidence_score': self.confidence_score.to_dict() if self.confidence_score else None,
            'clarification_rounds': self.clarification_rounds,
            'task_plan': self.task_plan.to_dict() if self.task_plan else None,
            'execution_results': {
                task_id: {
                    'success': result.success,
                    'result': str(result.result)[:500] if result.result else None,
                    'execution_time': result.execution_time,
                    'error': result.error,
                }
                for task_id, result in self.execution_results.items()
            },
            'final_output': self.final_output,
            'success': self.success,
            'error': self.error,
            'execution_time_seconds': self.execution_time_seconds,
            'trace_id': self.trace_id,
            'timestamp': self.timestamp,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def print_summary(self):
        """Print a human-readable summary."""
        print("\n" + "="*70)
        print("ORCHESTRATOR EXECUTION SUMMARY")
        print("="*70)
        print(f"Status: {'✓ SUCCESS' if self.success else '✗ FAILED'}")
        print(f"Execution Time: {self.execution_time_seconds:.2f}s")

        if self.confidence_score:
            print(f"\nConfidence Score: {self.confidence_score.overall:.2f}")
            print(f"  • Clarity: {self.confidence_score.clarity:.2f}")
            print(f"  • Completeness: {self.confidence_score.completeness:.2f}")
            print(f"  • Feasibility: {self.confidence_score.feasibility:.2f}")
            print(f"  • Specificity: {self.confidence_score.specificity:.2f}")

        if self.clarification_rounds > 0:
            print(f"\nClarification Rounds: {self.clarification_rounds}")

        if self.task_plan:
            print(f"\nTasks Planned: {len(self.task_plan.tasks)}")
            print(f"Complexity: {self.task_plan.estimated_complexity}")
            print(f"Estimated Time: {self.task_plan.estimated_time}")

        if self.execution_results:
            success_count = sum(1 for r in self.execution_results.values() if r.success)
            print(f"\nTasks Executed: {len(self.execution_results)}")
            print(f"  • Successful: {success_count}")
            print(f"  • Failed: {len(self.execution_results) - success_count}")

        if self.final_output:
            print(f"\nFinal Output:")
            print("-" * 70)
            print(self.final_output[:500] + "..." if len(self.final_output) > 500 else self.final_output)
            print("-" * 70)

        if self.error:
            print(f"\nError: {self.error}")

        if self.trace_id:
            print(f"\nTrace ID: {self.trace_id}")

        print("="*70 + "\n")


class Orchestrator:
    """
    Main orchestrator for agentic workflows.

    Coordinates confidence scoring, clarification, task planning,
    and execution to solve complex user requests.
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize orchestrator.

        Args:
            config: Orchestrator configuration. If None, uses default config.
        """
        from ..config import get_default_config

        self.config = config or get_default_config()
        self.logger = get_logger(__name__)

        # Validate configuration
        if not self.config.is_valid():
            validation_report = self.config.get_validation_report()
            self.logger.error(f"Invalid configuration:\n{validation_report}")
            raise ValueError(f"Invalid configuration:\n{validation_report}")

        # Initialize components
        self.model_manager = ModelManager(self.config.model)
        self.confidence_scorer = ConfidenceScorer(self.config.confidence, self.model_manager)
        self.clarification_handler = ClarificationHandler(
            self.config.confidence,
            self.model_manager
        )
        self.task_planner = TaskPlanner(self.config.execution, self.model_manager)
        self.task_executor = TaskExecutor(self.config.execution, self.model_manager)

        self.logger.info("Orchestrator initialized", metadata={
            "config_valid": True,
            "orchestrator_model": self.config.model.orchestrator_model,
            "confidence_threshold": self.config.confidence.min_confidence_threshold,
        })

    def process(self, user_query: str, context: Optional[str] = None) -> OrchestratorResult:
        """
        Process user request through the complete workflow.

        Args:
            user_query: User's request or question.
            context: Optional additional context.

        Returns:
            OrchestratorResult with complete execution details.
        """
        import time

        trace_manager = get_trace_manager()
        trace_id = trace_manager.start_trace(metadata={
            "query": user_query[:100],
            "context_provided": context is not None,
        })

        start_time = time.time()

        result = OrchestratorResult(
            original_query=user_query,
            trace_id=trace_id,
        )

        try:
            with trace_context("orchestrator_process", trace_id=trace_id, is_trace=False):
                self.logger.info("Processing user query", metadata={
                    "query_length": len(user_query),
                    "trace_id": trace_id,
                })

                # Stage 1: Confidence Assessment
                confidence_score = self._assess_confidence(user_query, context)
                result.confidence_score = confidence_score

                # Stage 2: Clarification (if needed)
                enhanced_query = user_query
                clarification_rounds = 0

                if not confidence_score.is_confident(self.config.confidence.min_confidence_threshold):
                    if self.config.confidence.auto_clarify:
                        enhanced_query, clarification_rounds = self._handle_clarification(
                            user_query,
                            confidence_score,
                            context
                        )
                        result.enhanced_query = enhanced_query
                        result.clarification_rounds = clarification_rounds
                    else:
                        result.success = False
                        result.error = "Confidence threshold not met and auto-clarification is disabled"
                        return result

                # Stage 3: Task Planning
                final_query = enhanced_query if enhanced_query else user_query
                task_plan = self._plan_tasks(final_query, context)
                result.task_plan = task_plan

                # Stage 4: Task Execution
                execution_results = self._execute_tasks(task_plan)
                result.execution_results = execution_results

                # Stage 5: Synthesize Final Output
                final_output = self._synthesize_output(
                    user_query,
                    task_plan,
                    execution_results
                )
                result.final_output = final_output

                # Mark as successful if all tasks succeeded
                result.success = all(r.success for r in execution_results.values())

                if not result.success:
                    failed_tasks = [
                        task_id for task_id, r in execution_results.items()
                        if not r.success
                    ]
                    result.error = f"Tasks failed: {', '.join(failed_tasks)}"

        except Exception as e:
            self.logger.error("Orchestrator process failed", metadata={
                "error": str(e),
            }, exc_info=True)

            result.success = False
            result.error = f"Orchestrator error: {str(e)}"

        finally:
            result.execution_time_seconds = time.time() - start_time
            trace_manager.end_trace(trace_id)

            self.logger.info("Orchestrator processing completed", metadata={
                "success": result.success,
                "execution_time": result.execution_time_seconds,
                "trace_id": trace_id,
            })

        return result

    def _assess_confidence(self, user_query: str, context: Optional[str]) -> ConfidenceScore:
        """Assess confidence in understanding the query."""
        with trace_context("assess_confidence"):
            self.logger.info("Assessing confidence")
            score = self.confidence_scorer.score(user_query, context)

            self.logger.info("Confidence assessed", metadata={
                "overall": score.overall,
                "is_confident": score.is_confident(self.config.confidence.min_confidence_threshold),
            })

            return score

    def _handle_clarification(
        self,
        user_query: str,
        confidence_score: ConfidenceScore,
        context: Optional[str]
    ) -> tuple[str, int]:
        """Handle clarification rounds."""
        with trace_context("handle_clarification"):
            self.logger.info("Starting clarification rounds")

            enhanced_query = user_query
            rounds = 0
            max_rounds = self.config.confidence.max_clarification_rounds

            for round_num in range(1, max_rounds + 1):
                rounds = round_num

                # Formulate questions
                questions = self.clarification_handler.formulate_questions(
                    confidence_score,
                    enhanced_query
                )

                if not questions:
                    self.logger.info("No clarification questions needed")
                    break

                # Ask questions and get enhanced query
                enhanced_query = self.clarification_handler.ask_clarifications(
                    questions,
                    enhanced_query
                )

                # Re-assess confidence
                confidence_score = self.confidence_scorer.score(enhanced_query, context)

                if confidence_score.is_confident(self.config.confidence.min_confidence_threshold):
                    self.logger.info(f"Confidence threshold met after {rounds} rounds")
                    break

            return enhanced_query, rounds

    def _plan_tasks(self, user_query: str, context: Optional[str]) -> TaskPlan:
        """Plan task breakdown."""
        with trace_context("plan_tasks"):
            self.logger.info("Planning tasks")

            clarification_context = self.clarification_handler.get_clarification_context()
            full_context = f"{context}\n\n{clarification_context}" if context else clarification_context

            task_plan = self.task_planner.plan(user_query, full_context)

            self.logger.info("Tasks planned", metadata={
                "task_count": len(task_plan.tasks),
                "complexity": task_plan.estimated_complexity,
            })

            return task_plan

    def _execute_tasks(self, task_plan: TaskPlan) -> Dict[str, ExecutionResult]:
        """Execute task plan."""
        with trace_context("execute_tasks"):
            self.logger.info("Executing tasks")

            results = self.task_executor.execute_plan(task_plan)

            success_count = sum(1 for r in results.values() if r.success)
            self.logger.info("Tasks executed", metadata={
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
            })

            return results

    def _synthesize_output(
        self,
        user_query: str,
        task_plan: TaskPlan,
        execution_results: Dict[str, ExecutionResult]
    ) -> str:
        """Synthesize final output from execution results."""
        with trace_context("synthesize_output"):
            self.logger.info("Synthesizing final output")

            # Collect successful task results
            results_text = []
            for task in task_plan.tasks:
                if task.task_id in execution_results:
                    exec_result = execution_results[task.task_id]
                    if exec_result.success:
                        results_text.append(
                            f"**{task.title}**\n{str(exec_result.result)}"
                        )

            combined_results = "\n\n".join(results_text)

            # Use AI to synthesize final response
            synthesis_prompt = f"""Given the user's request and the results from executing tasks, provide a comprehensive, well-structured response.

**User Request:**
{user_query}

**Task Results:**
{combined_results}

**Your Task:**
Synthesize a clear, complete response that directly addresses the user's request. Organize the information logically and ensure it's easy to understand.

Response:"""

            try:
                response = self.model_manager.orchestrator_generate(
                    prompt=synthesis_prompt,
                    temperature=0.5,
                )

                final_output = response.content

                self.logger.info("Output synthesized", metadata={
                    "output_length": len(final_output),
                })

                return final_output

            except Exception as e:
                self.logger.error("Failed to synthesize output", exc_info=True)
                # Fallback: return raw results
                return combined_results
