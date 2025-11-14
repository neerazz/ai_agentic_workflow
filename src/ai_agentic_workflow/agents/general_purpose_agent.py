"""
General Purpose Agent with critique-driven self-improvement.

Implements complete workflow: confidence → clarification → reasoning →
task execution → critique loops → synthesis.

Designed as extensible template for creating specialized agents.
"""

import uuid
from typing import Optional, Dict, Any, Callable

from .base_agent import BaseAgent, AgentResult
from .critique_engine import CritiqueEngine, CritiqueDecision
from .decision_maker import DecisionMaker
from .task_reasoner import TaskReasoner
from .progress_tracker import ProgressTracker, TaskProgress, WorkflowStage, TaskStatus

from ..orchestrator.confidence_scorer import ConfidenceScorer
from ..orchestrator.clarification_handler import ClarificationHandler
from ..orchestrator.task_executor import TaskExecutor
from ..config import OrchestratorConfig
from ..logging import get_logger, trace_context, get_trace_manager


class GeneralPurposeAgent(BaseAgent):
    """
    General-purpose agent with self-improving critique loops.

    Features:
    - Multi-dimensional confidence scoring
    - Intelligent clarification
    - Deep task reasoning (2-15 tasks)
    - Critique-driven quality improvement
    - Up to 3 retry attempts per task
    - Progress tracking for UI integration
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        user_input_callback: Optional[Callable[[str], str]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize general purpose agent.

        Args:
            config: Orchestrator configuration.
            user_input_callback: Optional callback for user input (for clarifications).
            progress_callback: Optional callback for progress updates (for UI).
        """
        super().__init__(config, name="GeneralPurposeAgent")

        # Initialize components
        self.confidence_scorer = ConfidenceScorer(config.confidence, self.model_manager)
        self.clarification_handler = ClarificationHandler(
            config.confidence,
            self.model_manager,
            user_input_callback
        )
        self.task_reasoner = TaskReasoner(self.model_manager)
        self.task_executor = TaskExecutor(config.execution, self.model_manager)
        self.critique_engine = CritiqueEngine(self.model_manager, config.confidence.min_confidence_threshold)
        self.decision_maker = DecisionMaker(self.model_manager, max_retries=3)
        self.progress_tracker = ProgressTracker()

        self.progress_callback = progress_callback

        self.logger.info("GeneralPurposeAgent fully initialized")

    def execute(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute the complete workflow with critique loops.

        Args:
            user_input: User's request/question.
            context: Optional execution context.

        Returns:
            AgentResult with final output and metadata.
        """
        # Validate input
        if not self.validate_input(user_input):
            return AgentResult(
                success=False,
                output=None,
                error="Invalid input provided"
            )

        # Start tracing
        trace_manager = get_trace_manager()
        trace_id = trace_manager.start_trace(metadata={"user_input": user_input[:100]})

        # Start progress tracking
        workflow_id = str(uuid.uuid4())
        progress = self.progress_tracker.start_workflow(workflow_id, user_input)
        self._notify_progress(progress)

        try:
            with trace_context("general_purpose_agent", trace_id=trace_id, is_trace=False):
                # Stage 1: Confidence Assessment
                self._update_stage(workflow_id, WorkflowStage.CLARIFYING)
                enhanced_query, clarification_context = self._assess_and_clarify(
                    user_input, context, workflow_id
                )

                # Stage 2: Task Reasoning and Planning
                self._update_stage(workflow_id, WorkflowStage.PLANNING)
                task_plan = self._reason_and_plan(enhanced_query, clarification_context, workflow_id)

                # Stage 3: Task Execution with Critique Loops
                self._update_stage(workflow_id, WorkflowStage.EXECUTING)
                execution_results = self._execute_with_critique(task_plan, workflow_id)

                # Stage 4: Final Critique
                self._update_stage(workflow_id, WorkflowStage.CRITIQUING)
                final_output = self._synthesize_output(user_input, task_plan, execution_results)

                final_critique = self.critique_engine.critique_final_output(
                    user_request=user_input,
                    final_output=final_output,
                    execution_context={
                        "tasks_completed": len(execution_results),
                        "execution_time": progress.elapsed_time(),
                    }
                )

                # Decide if output is acceptable
                if final_critique.decision == CritiqueDecision.ACCEPT:
                    success = True
                    self.logger.info(f"Final output accepted (score: {final_critique.quality_score:.2f})")
                else:
                    success = True  # Still return output even if not perfect
                    self.logger.warning(f"Final output has issues (score: {final_critique.quality_score:.2f})")

                # Complete workflow
                self._update_stage(workflow_id, WorkflowStage.COMPLETED)
                self.progress_tracker.complete_workflow(workflow_id, final_output, success)
                self._notify_progress(progress)

                trace_manager.end_trace(trace_id)

                return AgentResult(
                    success=success,
                    output=final_output,
                    metadata={
                        'workflow_id': workflow_id,
                        'trace_id': trace_id,
                        'final_critique': final_critique.to_dict(),
                        'tasks_executed': len(execution_results),
                        'execution_time': progress.elapsed_time(),
                        'progress': progress.to_dict(),
                    }
                )

        except Exception as e:
            self.logger.error(f"Workflow failed: {e}", exc_info=True)
            self._update_stage(workflow_id, WorkflowStage.FAILED)
            self.progress_tracker.complete_workflow(workflow_id, "", success=False)
            trace_manager.end_trace(trace_id)
            return self.handle_error(e)

    def _assess_and_clarify(
        self,
        user_input: str,
        context: Optional[Dict],
        workflow_id: str
    ) -> tuple[str, str]:
        """Assess confidence and clarify if needed."""
        with trace_context("assess_and_clarify"):
            self.logger.info("Assessing confidence")

            # Score confidence
            confidence_score = self.confidence_scorer.score(user_input, context)

            self.logger.info(f"Confidence: {confidence_score.overall:.2f}")

            # Clarify if needed
            if not confidence_score.is_confident(self.config.confidence.min_confidence_threshold):
                if self.config.confidence.auto_clarify:
                    self.logger.info("Confidence below threshold, starting clarification")

                    questions = self.clarification_handler.formulate_questions(
                        confidence_score,
                        user_input
                    )

                    if questions:
                        enhanced_query = self.clarification_handler.ask_clarifications(
                            questions,
                            user_input
                        )
                        clarification_context = self.clarification_handler.get_clarification_context()
                        return enhanced_query, clarification_context

            return user_input, ""

    def _reason_and_plan(self, query: str, context: str, workflow_id: str):
        """Deep reasoning and task planning."""
        with trace_context("reason_and_plan"):
            self.logger.info("Reasoning about task breakdown")

            task_plan = self.task_reasoner.reason_and_break_down(query, context)

            # Add tasks to progress tracker
            for task in task_plan.tasks:
                task_progress = TaskProgress(
                    task_id=task.task_id,
                    title=task.title,
                    description=task.description,
                    status=TaskStatus.PENDING,
                    max_attempts=3,
                )
                self.progress_tracker.add_task(workflow_id, task_progress)

            self._notify_progress(self.progress_tracker.workflows[workflow_id])

            return task_plan

    def _execute_with_critique(self, task_plan, workflow_id):
        """Execute tasks with critique loops (max 3 attempts)."""
        with trace_context("execute_with_critique"):
            execution_results = {}

            for task in task_plan.tasks:
                self.logger.info(f"Executing task: {task.task_id}")

                # Try up to 3 times
                for attempt in range(1, 4):
                    self.progress_tracker.start_task(workflow_id, task.task_id)
                    self._notify_progress(self.progress_tracker.workflows[workflow_id])

                    # Execute task
                    result = self.task_executor.execute_task(task)

                    # Critique the output
                    self.progress_tracker.critique_task(workflow_id, task.task_id)
                    self._notify_progress(self.progress_tracker.workflows[workflow_id])

                    critique = self.critique_engine.critique_task_output(
                        task_description=task.description,
                        expected_outcome=task.title,
                        actual_output=result.result,
                        success_criteria=task.success_criteria,
                    )

                    # Decide: proceed or retry?
                    decision = self.decision_maker.decide_on_task(
                        critique=critique,
                        attempt_number=attempt,
                        previous_critiques=[]  # Could track history
                    )

                    if decision.should_proceed:
                        # Task complete
                        self.progress_tracker.complete_task(
                            workflow_id,
                            task.task_id,
                            result.result,
                            critique.quality_score
                        )
                        execution_results[task.task_id] = result
                        self.logger.info(f"Task {task.task_id} completed (attempt {attempt}, score {critique.quality_score:.2f})")
                        break
                    else:
                        # Retry needed
                        self.logger.warning(f"Task {task.task_id} needs retry (attempt {attempt})")
                        self.progress_tracker.retry_task(workflow_id, task.task_id, attempt + 1)
                        self._notify_progress(self.progress_tracker.workflows[workflow_id])

                        # Update task with improvement suggestions
                        if critique.suggestions:
                            task.description += f"\n\nImprovement suggestions:\n" + "\n".join(f"- {s}" for s in critique.suggestions)

                else:
                    # Max retries reached
                    self.logger.warning(f"Task {task.task_id} reached max retries")
                    self.progress_tracker.complete_task(
                        workflow_id,
                        task.task_id,
                        result.result,
                        critique.quality_score
                    )
                    execution_results[task.task_id] = result

                self._notify_progress(self.progress_tracker.workflows[workflow_id])

            return execution_results

    def _synthesize_output(self, user_request, task_plan, execution_results):
        """Synthesize final output from task results."""
        with trace_context("synthesize_output"):
            # Collect results
            results_text = []
            for task in task_plan.tasks:
                if task.task_id in execution_results:
                    result = execution_results[task.task_id]
                    results_text.append(f"**{task.title}**\n{str(result.result)}")

            combined = "\n\n".join(results_text)

            # Synthesize using AI
            prompt = f"""Synthesize a comprehensive response from the following task results.

**User Request:** {user_request}

**Task Results:**
{combined}

Provide a clear, well-structured response that directly addresses the user's request.
"""

            try:
                response = self.model_manager.orchestrator_generate(prompt, temperature=0.5)
                return response.content
            except:
                return combined

    def _update_stage(self, workflow_id: str, stage: WorkflowStage):
        """Update workflow stage."""
        self.progress_tracker.update_stage(workflow_id, stage)
        self._notify_progress(self.progress_tracker.workflows[workflow_id])

    def _notify_progress(self, progress):
        """Notify progress callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(progress.to_dict())
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
