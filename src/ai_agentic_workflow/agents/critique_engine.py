"""
Critique Engine for harsh, unbiased evaluation of AI outputs.

Uses Groq models for fast, critical evaluation without favoritism.
Provides detailed feedback and improvement suggestions.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from ..llm.model_manager import ModelManager
from ..logging import get_logger, trace_context


class CritiqueDecision(str, Enum):
    """Decision outcomes from critique."""
    ACCEPT = "accept"  # Output meets quality standards
    RETRY = "retry"  # Output needs improvement, retry recommended
    REJECT = "reject"  # Output is fundamentally flawed, major rework needed


@dataclass
class CritiqueResult:
    """
    Result from critique evaluation.

    Contains harsh, objective assessment of output quality.
    """
    # Overall decision
    decision: CritiqueDecision

    # Quality score (0.0 - 1.0, where 1.0 is perfect)
    quality_score: float

    # Dimension-specific scores
    accuracy_score: float  # Factual correctness
    completeness_score: float  # Addresses all requirements
    clarity_score: float  # Clear and well-structured
    relevance_score: float  # Relevant to the task

    # Critical issues identified
    critical_issues: List[str] = field(default_factory=list)

    # Minor issues identified
    minor_issues: List[str] = field(default_factory=list)

    # Specific improvement suggestions
    suggestions: List[str] = field(default_factory=list)

    # Harsh critique comments
    critique_comments: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_acceptable(self, threshold: float = 0.75) -> bool:
        """Check if output meets quality threshold."""
        return self.decision == CritiqueDecision.ACCEPT and self.quality_score >= threshold

    def should_retry(self) -> bool:
        """Check if retry is recommended."""
        return self.decision == CritiqueDecision.RETRY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'decision': self.decision.value,
            'quality_score': self.quality_score,
            'accuracy_score': self.accuracy_score,
            'completeness_score': self.completeness_score,
            'clarity_score': self.clarity_score,
            'relevance_score': self.relevance_score,
            'critical_issues': self.critical_issues,
            'minor_issues': self.minor_issues,
            'suggestions': self.suggestions,
            'critique_comments': self.critique_comments,
            'is_acceptable': self.is_acceptable(),
            'metadata': self.metadata,
        }


class CritiqueEngine:
    """
    Harsh, unbiased critique engine for evaluating AI outputs.

    Uses Groq models for fast, critical evaluation without favoritism.
    Designed to be a "cut-throat critic" that demands excellence.
    """

    def __init__(self, model_manager: ModelManager, critique_threshold: float = 0.75):
        """
        Initialize critique engine.

        Args:
            model_manager: Model manager for AI calls.
            critique_threshold: Minimum acceptable quality score (0.0 - 1.0).
        """
        self.model_manager = model_manager
        self.critique_threshold = critique_threshold
        self.logger = get_logger(__name__)

        self.logger.info("CritiqueEngine initialized", metadata={
            "critique_threshold": critique_threshold,
        })

    def critique_task_output(
        self,
        task_description: str,
        expected_outcome: str,
        actual_output: Any,
        success_criteria: List[str],
        context: Optional[str] = None
    ) -> CritiqueResult:
        """
        Critique a task's output with harsh, objective evaluation.

        Args:
            task_description: Description of what the task should do.
            expected_outcome: What was expected from this task.
            actual_output: The actual output produced.
            success_criteria: List of criteria for success.
            context: Optional additional context.

        Returns:
            CritiqueResult with detailed evaluation.
        """
        with trace_context("critique_task_output") as span_id:
            self.logger.info("Critiquing task output", metadata={
                "task_length": len(task_description),
                "criteria_count": len(success_criteria),
            })

            # Build critique prompt
            prompt = self._build_task_critique_prompt(
                task_description,
                expected_outcome,
                actual_output,
                success_criteria,
                context
            )

            # Get harsh critique from Groq (fast and unbiased)
            try:
                response = self.model_manager.generate_with_provider(
                    provider_name=self.model_manager.config.executor_provider,
                    model=self.model_manager.config.executor_model,
                    prompt=prompt,
                    temperature=0.2,  # Low temperature for consistent evaluation
                    system_prompt="You are a harsh, unbiased critic. Be brutally honest and demanding. No favoritism, no sugarcoating. Point out every flaw and demand excellence."
                )

                # Parse critique response
                result = self._parse_critique_response(response.content)

                self.logger.info("Task critique completed", metadata={
                    "decision": result.decision.value,
                    "quality_score": result.quality_score,
                    "critical_issues": len(result.critical_issues),
                })

                return result

            except Exception as e:
                self.logger.error("Critique failed", metadata={
                    "error": str(e),
                }, exc_info=True)

                # Return conservative critique on error
                return CritiqueResult(
                    decision=CritiqueDecision.RETRY,
                    quality_score=0.5,
                    accuracy_score=0.5,
                    completeness_score=0.5,
                    clarity_score=0.5,
                    relevance_score=0.5,
                    critical_issues=["Failed to complete critique evaluation"],
                    suggestions=["Please retry the critique process"],
                )

    def critique_final_output(
        self,
        user_request: str,
        final_output: str,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> CritiqueResult:
        """
        Critique the final output against user's original request.

        Args:
            user_request: Original user request.
            final_output: Final synthesized output.
            execution_context: Optional context about execution.

        Returns:
            CritiqueResult with overall evaluation.
        """
        with trace_context("critique_final_output") as span_id:
            self.logger.info("Critiquing final output")

            prompt = self._build_final_critique_prompt(
                user_request,
                final_output,
                execution_context
            )

            try:
                response = self.model_manager.generate_with_provider(
                    provider_name=self.model_manager.config.orchestrator_provider,
                    model=self.model_manager.config.orchestrator_model,
                    prompt=prompt,
                    temperature=0.2,
                    system_prompt="You are a harsh, demanding critic evaluating whether this output truly satisfies the user's request. Be brutally honest. Demand excellence."
                )

                result = self._parse_critique_response(response.content)

                self.logger.info("Final critique completed", metadata={
                    "decision": result.decision.value,
                    "quality_score": result.quality_score,
                })

                return result

            except Exception as e:
                self.logger.error("Final critique failed", exc_info=True)

                return CritiqueResult(
                    decision=CritiqueDecision.RETRY,
                    quality_score=0.5,
                    accuracy_score=0.5,
                    completeness_score=0.5,
                    clarity_score=0.5,
                    relevance_score=0.5,
                    critical_issues=["Critique evaluation failed"],
                )

    def critique_task_plan(
        self,
        user_request: str,
        task_plan,  # TaskPlan object
        reasoning_context: Optional[str] = None
    ) -> CritiqueResult:
        """
        Critique the task breakdown plan before execution.

        Args:
            user_request: Original user request.
            task_plan: TaskPlan with breakdown.
            reasoning_context: Optional reasoning context.

        Returns:
            CritiqueResult evaluating the task plan quality.
        """
        with trace_context("critique_task_plan") as span_id:
            self.logger.info("Critiquing task plan", metadata={
                "task_count": len(task_plan.tasks),
            })

            prompt = self._build_task_plan_critique_prompt(
                user_request,
                task_plan,
                reasoning_context
            )

            try:
                response = self.model_manager.generate_with_provider(
                    provider_name=self.model_manager.config.planner_provider,
                    model=self.model_manager.config.planner_model,
                    prompt=prompt,
                    temperature=0.2,
                    system_prompt="You are a harsh critic evaluating task planning. Demand clarity, proper dependencies, and realistic success criteria. Be brutal about poor planning."
                )

                result = self._parse_critique_response(response.content)

                self.logger.info("Task plan critique completed", metadata={
                    "decision": result.decision.value,
                    "quality_score": result.quality_score,
                })

                return result

            except Exception as e:
                self.logger.error("Task plan critique failed", exc_info=True)

                return CritiqueResult(
                    decision=CritiqueDecision.RETRY,
                    quality_score=0.5,
                    accuracy_score=0.5,
                    completeness_score=0.5,
                    clarity_score=0.5,
                    relevance_score=0.5,
                    critical_issues=["Failed to critique task plan"],
                )

    def _build_task_plan_critique_prompt(
        self,
        user_request: str,
        task_plan,
        reasoning_context: Optional[str]
    ) -> str:
        """Build prompt for task plan critique."""
        tasks_summary = "\n".join([
            f"**Task {t.task_id}**: {t.title}\n"
            f"  Description: {t.description}\n"
            f"  Source: {t.source.value}\n"
            f"  Success Criteria: {', '.join(t.success_criteria)}\n"
            f"  Dependencies: {', '.join(t.dependencies) if t.dependencies else 'None'}\n"
            f"  Priority: {t.priority}"
            for t in task_plan.tasks
        ])

        prompt = f"""You are a HARSH CRITIC evaluating a task breakdown plan. Be BRUTAL about poor planning.

**User Request:**
{user_request}

**Proposed Task Plan:**
- Total tasks: {len(task_plan.tasks)}
- Estimated complexity: {task_plan.estimated_complexity}
- Estimated time: {task_plan.estimated_time}

**Tasks:**
{tasks_summary}
"""

        if reasoning_context:
            prompt += f"\n**Reasoning Context:**\n{reasoning_context}"

        prompt += """

**Evaluate This Task Plan:**

1. **Accuracy** (0.0-1.0): Are tasks correctly addressing the user's request?
2. **Completeness** (0.0-1.0): Do tasks cover everything needed?
3. **Clarity** (0.0-1.0): Are task descriptions clear and specific?
4. **Relevance** (0.0-1.0): Are all tasks necessary?

**Check for:**
- Are task counts reasonable (2-15)?
- Are dependencies correct and non-circular?
- Are success criteria measurable?
- Are tasks properly scoped (not too broad/narrow)?
- Is the execution order logical?
- Are there any redundant tasks?

**Critical Issues**: Major problems that MUST be fixed
**Minor Issues**: Things that could be improved
**Suggestions**: Specific improvements to the plan

**Decision:**
- ACCEPT: Plan is solid and ready for execution
- RETRY: Plan has issues, needs replanning
- REJECT: Plan is fundamentally flawed

**Response Format (JSON):**
```json
{
    "accuracy_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "critical_issues": ["list of critical problems with the plan"],
    "minor_issues": ["list of minor issues"],
    "suggestions": ["specific improvements to the plan"],
    "harsh_comments": "Your brutal assessment of this task plan",
    "decision": "accept|retry|reject"
}
```

Be HARSH. Bad planning leads to bad execution. Demand EXCELLENCE.
"""

        return prompt

    def _build_task_critique_prompt(
        self,
        task_description: str,
        expected_outcome: str,
        actual_output: Any,
        success_criteria: List[str],
        context: Optional[str]
    ) -> str:
        """Build prompt for task output critique."""
        prompt = f"""You are a HARSH, UNBIASED CRITIC. Your job is to brutally evaluate this task output. NO FAVORITISM. NO SUGARCOATING.

**Task Description:**
{task_description}

**Expected Outcome:**
{expected_outcome}

**Actual Output:**
{str(actual_output)[:2000]}

**Success Criteria:**
{chr(10).join(f"{i+1}. {criterion}" for i, criterion in enumerate(success_criteria))}
"""

        if context:
            prompt += f"""
**Additional Context:**
{context}
"""

        prompt += """
**Your Evaluation:**

Rate each dimension from 0.0 to 1.0 (where 1.0 is perfect):
1. **Accuracy**: Is this factually correct and truthful?
2. **Completeness**: Does it address ALL success criteria?
3. **Clarity**: Is it clear, well-structured, and understandable?
4. **Relevance**: Is it relevant to the task?

Then provide:
- **Critical Issues**: Major problems that MUST be fixed
- **Minor Issues**: Small problems that should be improved
- **Suggestions**: Specific, actionable improvements
- **Harsh Comments**: Your brutal, honest assessment

**Decision:**
- ACCEPT: Meets ALL criteria perfectly (be very strict!)
- RETRY: Has issues but can be improved with feedback
- REJECT: Fundamentally flawed, needs major rework

**IMPORTANT:** Be HARSH. Demand EXCELLENCE. Do NOT accept mediocrity.

**Response Format (JSON):**
```json
{
    "accuracy_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "critical_issues": ["list of critical problems"],
    "minor_issues": ["list of minor problems"],
    "suggestions": ["specific improvements needed"],
    "harsh_comments": "Your brutal, honest critique",
    "decision": "accept|retry|reject"
}
```

Respond ONLY with the JSON object. Be BRUTAL in your assessment.
"""

        return prompt

    def _build_final_critique_prompt(
        self,
        user_request: str,
        final_output: str,
        execution_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for final output critique."""
        prompt = f"""You are a HARSH, DEMANDING CRITIC evaluating the final output. Be BRUTALLY HONEST.

**User's Original Request:**
{user_request}

**Final Output:**
{final_output[:3000]}
"""

        if execution_context:
            prompt += f"""
**Execution Context:**
- Tasks completed: {execution_context.get('tasks_completed', 'unknown')}
- Total time: {execution_context.get('execution_time', 'unknown')}
"""

        prompt += """
**Your Evaluation:**

Does this output TRULY satisfy the user's request? Be HARSH. Demand EXCELLENCE.

Rate from 0.0 to 1.0:
1. **Accuracy**: Factually correct?
2. **Completeness**: Fully addresses the request?
3. **Clarity**: Clear and well-organized?
4. **Relevance**: Directly relevant?

Provide:
- **Critical Issues**: What's WRONG with this?
- **Minor Issues**: What could be better?
- **Suggestions**: How to improve it?
- **Harsh Comments**: Your brutal assessment

**Decision:**
- ACCEPT: Truly satisfies the request (be VERY strict!)
- RETRY: Needs improvement
- REJECT: Does NOT satisfy the request

**Response Format (JSON):**
```json
{
    "accuracy_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "critical_issues": ["major problems"],
    "minor_issues": ["minor problems"],
    "suggestions": ["improvements"],
    "harsh_comments": "Your brutal critique",
    "decision": "accept|retry|reject"
}
```

Be HARSH. NO MERCY. Demand PERFECTION.
"""

        return prompt

    def _parse_critique_response(self, response_text: str) -> CritiqueResult:
        """Parse AI response into CritiqueResult."""
        try:
            # Extract JSON
            json_text = response_text.strip()

            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text
                json_text = json_text.replace("```json", "").replace("```", "").strip()

            # Parse JSON
            data = json.loads(json_text)

            # Extract scores
            accuracy = float(data.get('accuracy_score', 0.5))
            completeness = float(data.get('completeness_score', 0.5))
            clarity = float(data.get('clarity_score', 0.5))
            relevance = float(data.get('relevance_score', 0.5))

            # Calculate overall quality score (weighted average)
            quality_score = (
                accuracy * 0.35 +
                completeness * 0.35 +
                clarity * 0.15 +
                relevance * 0.15
            )

            # Parse decision
            decision_str = data.get('decision', 'retry').lower()
            if decision_str == 'accept':
                decision = CritiqueDecision.ACCEPT
            elif decision_str == 'reject':
                decision = CritiqueDecision.REJECT
            else:
                decision = CritiqueDecision.RETRY

            return CritiqueResult(
                decision=decision,
                quality_score=quality_score,
                accuracy_score=accuracy,
                completeness_score=completeness,
                clarity_score=clarity,
                relevance_score=relevance,
                critical_issues=data.get('critical_issues', []),
                minor_issues=data.get('minor_issues', []),
                suggestions=data.get('suggestions', []),
                critique_comments=data.get('harsh_comments', ''),
            )

        except Exception as e:
            self.logger.error("Failed to parse critique response", metadata={
                "error": str(e),
                "response": response_text[:500],
            }, exc_info=True)

            # Return conservative critique
            return CritiqueResult(
                decision=CritiqueDecision.RETRY,
                quality_score=0.5,
                accuracy_score=0.5,
                completeness_score=0.5,
                clarity_score=0.5,
                relevance_score=0.5,
                critical_issues=["Failed to parse critique evaluation"],
                suggestions=["Please retry critique"],
            )
