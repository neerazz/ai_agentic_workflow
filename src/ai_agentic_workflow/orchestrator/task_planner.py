"""
AI-powered task planning and breakdown.

Analyzes user requests and breaks them down into executable tasks
with dependencies, sources, and success criteria.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from ..config.orchestrator_config import ExecutionConfig
from ..logging import get_logger, trace_context
from ..llm.model_manager import ModelManager


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskSource(str, Enum):
    """Source type for task execution."""
    LLM_GENERATION = "llm_generation"  # Use AI model to generate response
    DATABASE_QUERY = "database_query"  # Query a database
    API_CALL = "api_call"  # Make an external API call
    WEB_SEARCH = "web_search"  # Perform web search
    CODE_EXECUTION = "code_execution"  # Execute code
    FILE_OPERATION = "file_operation"  # Read/write files
    HUMAN_INPUT = "human_input"  # Requires human input
    COMPOSITE = "composite"  # Combines multiple sources


@dataclass
class Task:
    """Represents a single executable task."""

    # Task identification
    task_id: str
    title: str
    description: str

    # Execution details
    source: TaskSource
    source_details: Dict[str, Any]  # Source-specific parameters

    # Success criteria
    success_criteria: List[str]

    # Dependencies and ordering
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    priority: int = 1  # 1 = highest

    # Status tracking
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self, completed_tasks: List[str]) -> bool:
        """Check if task dependencies are satisfied."""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'source': self.source.value,
            'source_details': self.source_details,
            'success_criteria': self.success_criteria,
            'dependencies': self.dependencies,
            'priority': self.priority,
            'status': self.status.value,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'metadata': self.metadata,
        }


@dataclass
class TaskPlan:
    """Complete plan with all tasks."""
    tasks: List[Task]
    estimated_complexity: str  # "simple", "moderate", "complex"
    estimated_time: str  # Human-readable estimate
    warnings: List[str] = field(default_factory=list)

    def get_ready_tasks(self, completed_task_ids: List[str]) -> List[Task]:
        """Get all tasks that are ready to execute."""
        return [
            task for task in self.tasks
            if task.status == TaskStatus.PENDING and task.is_ready(completed_task_ids)
        ]

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'task_count': len(self.tasks),
            'estimated_complexity': self.estimated_complexity,
            'estimated_time': self.estimated_time,
            'warnings': self.warnings,
        }


class TaskPlanner:
    """
    AI-powered task planning and breakdown.

    Analyzes complex requests and breaks them into executable
    tasks with clear dependencies and success criteria.
    """

    def __init__(self, config: ExecutionConfig, model_manager: ModelManager):
        """
        Initialize task planner.

        Args:
            config: Execution configuration.
            model_manager: Model manager for AI calls.
        """
        self.config = config
        self.model_manager = model_manager
        self.logger = get_logger(__name__)

        self.logger.info("TaskPlanner initialized", metadata={
            "strategy": config.strategy.value,
        })

    def plan(self, user_request: str, context: Optional[str] = None) -> TaskPlan:
        """
        Create execution plan for user request.

        Args:
            user_request: The user's request or problem.
            context: Optional additional context.

        Returns:
            TaskPlan with breakdown of tasks.
        """
        with trace_context("task_planning") as span_id:
            self.logger.info("Planning task breakdown", metadata={
                "request_length": len(user_request),
                "has_context": context is not None,
            })

            # Build planning prompt
            prompt = self._build_planning_prompt(user_request, context)

            try:
                # Get AI-generated plan
                response = self.model_manager.planner_generate(
                    prompt=prompt,
                    temperature=0.3,  # Lower temperature for consistent structure
                )

                # Parse response into TaskPlan
                task_plan = self._parse_plan(response.content)

                self.logger.info("Task plan created", metadata={
                    "task_count": len(task_plan.tasks),
                    "complexity": task_plan.estimated_complexity,
                    "warnings_count": len(task_plan.warnings),
                })

                return task_plan

            except Exception as e:
                self.logger.error("Task planning failed", metadata={
                    "error": str(e),
                }, exc_info=True)

                # Return simple fallback plan
                return self._create_fallback_plan(user_request)

    def _build_planning_prompt(self, user_request: str, context: Optional[str]) -> str:
        """Build the planning prompt for AI."""
        prompt = f"""You are an expert at breaking down complex problems into executable tasks.

**User Request:**
{user_request}
"""

        if context:
            prompt += f"""
**Additional Context:**
{context}
"""

        prompt += """
**Your Task:**
Break this request into a series of concrete, executable tasks. For each task, identify:

1. **Task Title**: Brief, descriptive title
2. **Description**: What needs to be done
3. **Source**: How to accomplish it. Choose from:
   - llm_generation: Use AI to generate response
   - database_query: Query a database
   - api_call: Call an external API
   - web_search: Search the web
   - code_execution: Execute code
   - file_operation: Read/write files
   - human_input: Requires human input
   - composite: Combines multiple approaches

4. **Source Details**: Specific parameters for the source (e.g., which API, what to search for)
5. **Success Criteria**: How to verify the task succeeded (list of checkpoints)
6. **Dependencies**: Task IDs this depends on (use T1, T2, etc.)
7. **Priority**: 1-5 (1 = highest priority)

Also provide:
- **Complexity**: "simple", "moderate", or "complex"
- **Estimated Time**: Rough human-readable estimate
- **Warnings**: Any concerns or limitations

**Response Format (JSON):**
```json
{
    "tasks": [
        {
            "task_id": "T1",
            "title": "Task title",
            "description": "What to do",
            "source": "llm_generation",
            "source_details": {
                "key": "value"
            },
            "success_criteria": [
                "Criterion 1",
                "Criterion 2"
            ],
            "dependencies": [],
            "priority": 1
        }
    ],
    "estimated_complexity": "moderate",
    "estimated_time": "5-10 minutes",
    "warnings": ["Warning if any"]
}
```

Respond ONLY with the JSON object, no additional text.
"""

        return prompt

    def _parse_plan(self, response_text: str) -> TaskPlan:
        """Parse AI response into TaskPlan."""
        try:
            # Extract JSON from response
            json_text = response_text.strip()

            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text
                json_text = json_text.replace("```json", "").replace("```", "").strip()

            # Parse JSON
            data = json.loads(json_text)

            # Create Task objects
            tasks = []
            for task_data in data.get('tasks', []):
                try:
                    task = Task(
                        task_id=task_data['task_id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        source=TaskSource(task_data['source']),
                        source_details=task_data.get('source_details', {}),
                        success_criteria=task_data.get('success_criteria', []),
                        dependencies=task_data.get('dependencies', []),
                        priority=task_data.get('priority', 1),
                    )
                    tasks.append(task)
                except Exception as e:
                    self.logger.warning(f"Failed to parse task: {e}", metadata={
                        "task_data": task_data,
                    })

            # Create TaskPlan
            task_plan = TaskPlan(
                tasks=tasks,
                estimated_complexity=data.get('estimated_complexity', 'moderate'),
                estimated_time=data.get('estimated_time', 'unknown'),
                warnings=data.get('warnings', []),
            )

            return task_plan

        except Exception as e:
            self.logger.error("Failed to parse task plan", metadata={
                "error": str(e),
                "response": response_text[:500],
            }, exc_info=True)

            raise

    def _create_fallback_plan(self, user_request: str) -> TaskPlan:
        """Create a simple fallback plan when parsing fails."""
        self.logger.warning("Using fallback task plan")

        return TaskPlan(
            tasks=[
                Task(
                    task_id="T1",
                    title="Process user request",
                    description=user_request,
                    source=TaskSource.LLM_GENERATION,
                    source_details={"prompt": user_request},
                    success_criteria=["Response generated", "Response is relevant"],
                    priority=1,
                )
            ],
            estimated_complexity="unknown",
            estimated_time="unknown",
            warnings=["Fallback plan - original planning failed"],
        )
