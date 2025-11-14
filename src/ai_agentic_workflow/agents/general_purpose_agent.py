"""
General Purpose Agent with critique-driven self-improvement and conversation memory.

Implements complete workflow with ALL critique loops:
- Task planning critique
- Task execution critique
- Final synthesis critique

Plus conversation context management for multi-turn interactions.
"""

import uuid
from typing import Optional, Dict, Any, Callable

from .base_agent import BaseAgent, AgentResult
from .critique_engine import CritiqueEngine, CritiqueDecision
from .decision_maker import DecisionMaker
from .task_reasoner import TaskReasoner
from .progress_tracker import ProgressTracker, TaskProgress, WorkflowStage, TaskStatus
from .conversation_manager import ConversationManager

from ..orchestrator.confidence_scorer import ConfidenceScorer
from ..orchestrator.clarification_handler import ClarificationHandler
from ..orchestrator.task_executor import TaskExecutor
from ..config import OrchestratorConfig
from ..logging import get_logger, trace_context, get_trace_manager


class GeneralPurposeAgent(BaseAgent):
    """
    General-purpose agent with self-improving critique loops and conversation memory.

    Features:
    - Multi-dimensional confidence scoring
    - Intelligent clarification
    - Deep task reasoning (2-15 tasks) WITH CRITIQUE
    - Task execution WITH CRITIQUE (up to 3 retries per task)
    - Final synthesis WITH CRITIQUE (up to 3 retries)
    - Conversation context management (Q&A only, no reasoning details)
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
        self.conversation_manager = ConversationManager(
            max_history_turns=10,
            max_context_tokens=4000
        )

        self.progress_callback = progress_callback

        self.logger.info("GeneralPurposeAgent fully initialized with conversation memory")

    def execute(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute the complete workflow with ALL critique loops and conversation context.

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
                # Get conversation context (Q&A only, no reasoning)
                conversation_context = self.conversation_manager.get_context_for_new_request(user_input)

                # Stage 1: Confidence Assessment & Clarification
                self._update_stage(workflow_id, WorkflowStage.CLARIFYING)
                enhanced_query, clarification_context = self._assess_and_clarify(
                    user_input, conversation_context, workflow_id
                )

                # Stage 2: Task Reasoning & Planning WITH CRITIQUE LOOP (max 3 attempts)
                self._update_stage(workflow_id, WorkflowStage.PLANNING)
                task_plan = self._reason_and_plan_with_critique(
                    enhanced_query,
                    conversation_context,
                    clarification_context,
                    workflow_id
                )

                # Stage 3: Task Execution with Critique Loops
                self._update_stage(workflow_id, WorkflowStage.EXECUTING)
                execution_results = self._execute_with_critique(task_plan, workflow_id)

                # Stage 4: Synthesis WITH CRITIQUE LOOP (max 3 attempts)
                self._update_stage(workflow_id, WorkflowStage.SYNTHESIZING)
                final_output = self._synthesize_with_critique(
                    user_input,
                    task_plan,
                    execution_results,
                    conversation_context,
                    workflow_id
                )

                # Complete workflow
                self._update_stage(workflow_id, WorkflowStage.COMPLETED)
                self.progress_tracker.complete_workflow(workflow_id, final_output, success=True)
                self._notify_progress(progress)

                # Add to conversation history (Q&A ONLY, no reasoning/tasks)
                self.conversation_manager.add_turn(
                    user_query=user_input,
                    ai_response=final_output,
                    metadata={
                        'workflow_id': workflow_id,
                        'execution_time': progress.elapsed_time(),
                    }
                )

                trace_manager.end_trace(trace_id)

                return AgentResult(
                    success=True,
                    output=final_output,
                    metadata={
                        'workflow_id': workflow_id,
                        'trace_id': trace_id,
                        'tasks_executed': len(execution_results),
                        'execution_time': progress.elapsed_time(),
                        'conversation_turn': len(self.conversation_manager.turns),
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
        conversation_context: str,
        workflow_id: str
    ) -> tuple[str, str]:
        """Assess confidence and clarify if needed."""
        with trace_context("assess_and_clarify"):
            self.logger.info("Assessing confidence")

            # Include conversation context in confidence assessment
            full_context = conversation_context if conversation_context else None

            # Score confidence
            confidence_score = self.confidence_scorer.score(user_input, full_context)

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

    def _reason_and_plan_with_critique(
        self,
        query: str,
        conversation_context: str,
        clarification_context: str,
        workflow_id: str
    ):
        """
        Deep reasoning and task planning WITH CRITIQUE LOOP.

        Tries up to 3 times to create an acceptable plan.
        """
        with trace_context("reason_and_plan_with_critique"):
            self.logger.info("Reasoning about task breakdown with critique")

            # Combine contexts
            full_context = f"{conversation_context}\n\n{clarification_context}" if clarification_context else conversation_context

            task_plan = None
            plan_critiques = []

            # Try up to 3 times to get an acceptable plan
            for attempt in range(1, 4):
                self.logger.info(f"Task planning attempt {attempt}/3")

                # Generate task plan
                task_plan = self.task_reasoner.reason_and_break_down(query, full_context)

                # Critique the plan
                plan_critique = self.critique_engine.critique_task_plan(
                    user_request=query,
                    task_plan=task_plan,
                    reasoning_context=full_context
                )

                plan_critiques.append(plan_critique)

                # Decision: accept or retry?
                decision = self.decision_maker.decide_on_task(
                    critique=plan_critique,
                    attempt_number=attempt,
                    previous_critiques=plan_critiques[:-1]
                )

                if decision.should_proceed:
                    self.logger.info(f"Task plan accepted (attempt {attempt}, score: {plan_critique.quality_score:.2f})")
                    break
                else:
                    self.logger.warning(f"Task plan needs improvement (attempt {attempt})")

                    # If not last attempt, incorporate feedback
                    if attempt < 3:
                        # Add improvement guidance to context
                        improvement_context = f"\n\nPrevious plan issues:\n" + "\n".join(f"- {issue}" for issue in plan_critique.critical_issues + plan_critique.minor_issues)
                        improvement_context += f"\n\nSuggestions:\n" + "\n".join(f"- {sug}" for sug in plan_critique.suggestions)

                        full_context += improvement_context
            else:
                # Max attempts reached - proceed with best plan
                self.logger.warning("Max planning attempts reached, proceeding with last plan")

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
        """Execute tasks with critique loops (max 3 attempts per task)."""
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
                        previous_critiques=[]
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

    def _synthesize_with_critique(
        self,
        user_request: str,
        task_plan,
        execution_results,
        conversation_context: str,
        workflow_id: str
    ):
        """
        Synthesize final output WITH CRITIQUE LOOP.

        Tries up to 3 times to create an acceptable final output.
        """
        with trace_context("synthesize_with_critique"):
            self.logger.info("Synthesizing final output with critique")

            final_output = None
            synthesis_critiques = []

            # Try up to 3 times
            for attempt in range(1, 4):
                self.logger.info(f"Synthesis attempt {attempt}/3")

                # Synthesize output
                final_output = self._synthesize_output(
                    user_request,
                    task_plan,
                    execution_results,
                    conversation_context
                )

                # Critique the final output
                final_critique = self.critique_engine.critique_final_output(
                    user_request=user_request,
                    final_output=final_output,
                    execution_context={
                        "tasks_completed": len(execution_results),
                        "conversation_context": conversation_context,
                    }
                )

                synthesis_critiques.append(final_critique)

                # Decision: accept or retry?
                decision = self.decision_maker.decide_on_task(
                    critique=final_critique,
                    attempt_number=attempt,
                    previous_critiques=synthesis_critiques[:-1]
                )

                if decision.should_proceed:
                    self.logger.info(f"Final output accepted (attempt {attempt}, score: {final_critique.quality_score:.2f})")
                    break
                else:
                    self.logger.warning(f"Final output needs improvement (attempt {attempt})")

                    # If not last attempt, try again with feedback
                    if attempt < 3:
                        # For now, we'll just retry synthesis
                        # Could add explicit improvement prompting here
                        pass
            else:
                self.logger.warning("Max synthesis attempts reached, using last output")

            return final_output

    def _synthesize_output(
        self,
        user_request: str,
        task_plan,
        execution_results,
        conversation_context: str
    ):
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
"""

            if conversation_context:
                prompt += f"\n{conversation_context}\n"

            prompt += f"""
**Task Results:**
{combined}

Provide a clear, well-structured response that directly addresses the user's request.
If this is a follow-up question, ensure your response builds on the previous conversation.
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

    def get_conversation_history(self):
        """Get full conversation history."""
        return self.conversation_manager.get_full_history()

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_manager.clear_history()
        self.logger.info("Conversation history cleared")
