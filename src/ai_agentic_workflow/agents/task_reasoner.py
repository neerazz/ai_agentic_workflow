"""
Task Reasoner for deep, intelligent task breakdown.

Analyzes user requests and breaks them down into 2-15 optimal tasks
with detailed reasoning about approach, dependencies, and execution strategy.
"""

import json
from typing import List, Optional, Dict, Any

from ..orchestrator.task_planner import Task, TaskPlan, TaskSource, TaskStatus
from ..llm.model_manager import ModelManager
from ..logging import get_logger, trace_context


class TaskReasoner:
    """
    Deep task reasoning and breakdown engine.

    Performs multi-stage reasoning to optimally break down complex
    requests into 2-15 executable tasks with clear dependencies.
    """

    def __init__(self, model_manager: ModelManager):
        """
        Initialize task reasoner.

        Args:
            model_manager: Model manager for AI calls.
        """
        self.model_manager = model_manager
        self.logger = get_logger(__name__)
        self.min_tasks = 2
        self.max_tasks = 15

        self.logger.info("TaskReasoner initialized", metadata={
            "task_range": f"{self.min_tasks}-{self.max_tasks}",
        })

    def reason_and_break_down(
        self,
        user_request: str,
        clarification_context: Optional[str] = None
    ) -> TaskPlan:
        """
        Perform deep reasoning and break down request into tasks.

        Args:
            user_request: User's request (possibly enhanced with clarifications).
            clarification_context: Optional clarification Q&A context.

        Returns:
            TaskPlan with 2-15 optimized tasks.
        """
        with trace_context("task_reasoning") as span_id:
            self.logger.info("Reasoning about task breakdown")

            # Stage 1: Understand the request deeply
            understanding = self._deep_understanding(user_request, clarification_context)

            # Stage 2: Determine optimal task breakdown strategy
            strategy = self._determine_strategy(user_request, understanding)

            # Stage 3: Break down into specific tasks
            tasks = self._break_into_tasks(user_request, understanding, strategy)

            # Stage 4: Optimize and validate task plan
            optimized_plan = self._optimize_plan(tasks)

            self.logger.info(f"Task breakdown complete: {len(optimized_plan.tasks)} tasks")

            return optimized_plan

    def _deep_understanding(self, request: str, context: Optional[str]) -> Dict[str, Any]:
        """Deep analysis of what the request is really asking for."""
        prompt = f"""Analyze this request deeply to understand the TRUE intent and requirements.

**Request:** {request}
"""

        if context:
            prompt += f"\n**Clarification Context:** {context}"

        prompt += """

Provide deep analysis:
1. What is the CORE goal?
2. What are the KEY requirements?
3. What constraints exist?
4. What's the expected outcome format?
5. What level of detail is needed?

Respond with JSON:
```json
{
    "core_goal": "...",
    "key_requirements": ["..."],
    "constraints": ["..."],
    "expected_format": "...",
    "detail_level": "high|medium|low",
    "complexity_estimate": "simple|moderate|complex"
}
```
"""

        try:
            response = self.model_manager.planner_generate(prompt, temperature=0.3)
            understanding = json.loads(self._extract_json(response.content))
            return understanding
        except:
            return {
                "core_goal": request,
                "key_requirements": [],
                "constraints": [],
                "expected_format": "text",
                "detail_level": "medium",
                "complexity_estimate": "moderate"
            }

    def _determine_strategy(self, request: str, understanding: Dict) -> Dict[str, Any]:
        """Determine the optimal task breakdown strategy."""
        complexity = understanding.get("complexity_estimate", "moderate")

        # Simple: 2-4 tasks
        # Moderate: 4-8 tasks
        # Complex: 8-15 tasks

        if complexity == "simple":
            target_tasks = (2, 4)
        elif complexity == "complex":
            target_tasks = (8, 15)
        else:
            target_tasks = (4, 8)

        return {
            "target_task_range": target_tasks,
            "approach": "sequential" if complexity == "simple" else "parallel-capable",
            "validation_needed": complexity != "simple",
        }

    def _break_into_tasks(
        self,
        request: str,
        understanding: Dict,
        strategy: Dict
    ) -> List[Task]:
        """Break request into specific, executable tasks."""
        min_t, max_t = strategy["target_task_range"]

        prompt = f"""Break this request into {min_t}-{max_t} SPECIFIC, EXECUTABLE tasks.

**Request:** {request}

**Understanding:**
- Core goal: {understanding.get('core_goal')}
- Requirements: {', '.join(understanding.get('key_requirements', []))}

**Rules:**
1. Each task must be CLEAR and SPECIFIC
2. Tasks should be INDEPENDENTLY EXECUTABLE
3. Include task dependencies
4. Specify HOW to execute each task (source)
5. Define SUCCESS CRITERIA for each task

**Task Sources:** llm_generation, api_call, web_search, database_query, code_execution, file_operation, composite

**Response Format (JSON):**
```json
{
    "tasks": [
        {
            "id": "T1",
            "title": "Clear task title",
            "description": "Specific what and how",
            "source": "llm_generation",
            "source_details": {"key": "value"},
            "success_criteria": ["criterion 1", "criterion 2"],
            "dependencies": [],
            "priority": 1
        }
    ],
    "estimated_complexity": "simple|moderate|complex",
    "estimated_time": "X-Y minutes"
}
```

Respond ONLY with JSON. Be SPECIFIC and ACTIONABLE.
"""

        try:
            response = self.model_manager.planner_generate(prompt, temperature=0.3)
            data = json.loads(self._extract_json(response.content))

            tasks = []
            for task_data in data.get("tasks", []):
                task = Task(
                    task_id=task_data.get("id", f"T{len(tasks)+1}"),
                    title=task_data.get("title", "Untitled task"),
                    description=task_data.get("description", ""),
                    source=TaskSource(task_data.get("source", "llm_generation")),
                    source_details=task_data.get("source_details", {}),
                    success_criteria=task_data.get("success_criteria", []),
                    dependencies=task_data.get("dependencies", []),
                    priority=task_data.get("priority", 1),
                )
                tasks.append(task)

            return tasks

        except Exception as e:
            self.logger.error(f"Task breakdown failed: {e}", exc_info=True)
            # Fallback: single task
            return [
                Task(
                    task_id="T1",
                    title="Process user request",
                    description=request,
                    source=TaskSource.LLM_GENERATION,
                    source_details={"prompt": request},
                    success_criteria=["Response generated", "Addresses user request"],
                    priority=1,
                )
            ]

    def _optimize_plan(self, tasks: List[Task]) -> TaskPlan:
        """Optimize and validate the task plan."""
        # Ensure task count is within bounds
        if len(tasks) < self.min_tasks:
            self.logger.warning(f"Only {len(tasks)} tasks, below minimum {self.min_tasks}")
        elif len(tasks) > self.max_tasks:
            self.logger.warning(f"{len(tasks)} tasks exceeds maximum {self.max_tasks}, trimming")
            tasks = tasks[:self.max_tasks]

        # Create plan
        plan = TaskPlan(
            tasks=tasks,
            estimated_complexity="moderate" if len(tasks) <= 8 else "complex",
            estimated_time=f"{len(tasks) * 2}-{len(tasks) * 5} minutes",
            warnings=[]
        )

        # Validate dependencies
        task_ids = {t.task_id for t in tasks}
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    plan.warnings.append(f"Task {task.task_id} has invalid dependency: {dep_id}")

        return plan

    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        return text.replace("```json", "").replace("```", "").strip()
