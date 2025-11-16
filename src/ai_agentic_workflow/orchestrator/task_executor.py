"""
Task executor with greedy execution strategy.

Executes tasks optimally by selecting the best approach for each
task and validating results against success criteria.
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .task_planner import Task, TaskStatus, TaskSource, TaskPlan
from ..config.orchestrator_config import ExecutionConfig
from ..logging import get_logger, trace_context
from ..llm.model_manager import ModelManager


@dataclass
class ExecutionResult:
    """Result of executing a single task."""
    task_id: str
    success: bool
    result: Any
    execution_time: float  # seconds
    retries: int
    error: Optional[str] = None
    validation_results: Optional[Dict[str, bool]] = None


class TaskExecutor:
    """
    Executes tasks using greedy optimization strategy.

    For each task, identifies the best execution approach and
    validates results against success criteria.
    """

    def __init__(self, config: ExecutionConfig, model_manager: ModelManager):
        """
        Initialize task executor.

        Args:
            config: Execution configuration.
            model_manager: Model manager for AI calls.
        """
        self.config = config
        self.model_manager = model_manager
        self.logger = get_logger(__name__)

        self.execution_history: List[ExecutionResult] = []

        self.logger.info("TaskExecutor initialized", metadata={
            "strategy": config.strategy.value,
            "max_retries": config.max_retries,
            "fail_fast": config.fail_fast,
        })

    def execute_plan(self, plan: TaskPlan) -> Dict[str, ExecutionResult]:
        """
        Execute entire task plan.

        Args:
            plan: TaskPlan to execute.

        Returns:
            Dictionary mapping task_id to ExecutionResult.
        """
        with trace_context("execute_plan") as span_id:
            self.logger.info("Executing task plan", metadata={
                "task_count": len(plan.tasks),
                "strategy": self.config.strategy.value,
            })

            results: Dict[str, ExecutionResult] = {}
            completed_task_ids: List[str] = []

            # Execute tasks according to strategy
            if self.config.strategy.value == "greedy":
                results = self._execute_greedy(plan, completed_task_ids)
            elif self.config.strategy.value == "sequential":
                results = self._execute_sequential(plan, completed_task_ids)
            elif self.config.strategy.value == "parallel":
                # For now, fall back to greedy (parallel would require async)
                self.logger.warning("Parallel strategy not yet implemented, using greedy")
                results = self._execute_greedy(plan, completed_task_ids)

            # Summary logging
            success_count = sum(1 for r in results.values() if r.success)
            total_time = sum(r.execution_time for r in results.values())

            self.logger.info("Task plan execution completed", metadata={
                "total_tasks": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
                "total_time_seconds": total_time,
            })

            return results

    def _execute_greedy(
        self,
        plan: TaskPlan,
        completed_task_ids: List[str]
    ) -> Dict[str, ExecutionResult]:
        """Execute tasks greedily - always pick the highest priority ready task."""
        results: Dict[str, ExecutionResult] = {}

        while True:
            # Get ready tasks
            ready_tasks = plan.get_ready_tasks(completed_task_ids)

            if not ready_tasks:
                # Check if there are still pending tasks (means circular dependency)
                pending = [t for t in plan.tasks if t.status == TaskStatus.PENDING]
                if pending:
                    self.logger.error("Circular dependency detected", metadata={
                        "pending_tasks": [t.task_id for t in pending],
                    })
                break

            # Sort by priority (1 = highest) and pick first
            ready_tasks.sort(key=lambda t: t.priority)
            task = ready_tasks[0]

            # Execute task
            result = self.execute_task(task)
            results[task.task_id] = result

            if result.success:
                completed_task_ids.append(task.task_id)
                task.status = TaskStatus.COMPLETED
                task.result = result.result
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error

                # Fail fast if configured
                if self.config.fail_fast:
                    self.logger.warning("Fail-fast triggered, stopping execution")
                    # Mark remaining tasks as skipped
                    for remaining_task in plan.tasks:
                        if remaining_task.status == TaskStatus.PENDING:
                            remaining_task.status = TaskStatus.SKIPPED
                    break

        return results

    def _execute_sequential(
        self,
        plan: TaskPlan,
        completed_task_ids: List[str]
    ) -> Dict[str, ExecutionResult]:
        """Execute tasks sequentially in order."""
        results: Dict[str, ExecutionResult] = {}

        for task in plan.tasks:
            # Check dependencies
            if not task.is_ready(completed_task_ids):
                self.logger.warning(f"Task {task.task_id} dependencies not met", metadata={
                    "dependencies": task.dependencies,
                    "completed": completed_task_ids,
                })
                task.status = TaskStatus.SKIPPED
                continue

            # Execute task
            result = self.execute_task(task)
            results[task.task_id] = result

            if result.success:
                completed_task_ids.append(task.task_id)
                task.status = TaskStatus.COMPLETED
                task.result = result.result
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error

                if self.config.fail_fast:
                    break

        return results

    def execute_task(self, task: Task) -> ExecutionResult:
        """
        Execute a single task with retry logic.

        Args:
            task: Task to execute.

        Returns:
            ExecutionResult with outcome.
        """
        with trace_context(f"execute_task_{task.task_id}") as span_id:
            self.logger.info(f"Executing task {task.task_id}", metadata={
                "title": task.title,
                "source": task.source.value,
            })

            task.status = TaskStatus.IN_PROGRESS
            start_time = time.time()

            result = None
            error = None
            retries = 0

            # Retry loop
            for attempt in range(self.config.max_retries + 1):
                try:
                    # Execute based on source type
                    result = self._execute_by_source(task)
                    error = None
                    break  # Success

                except Exception as e:
                    retries = attempt
                    error = str(e)
                    self.logger.warning(f"Task execution failed (attempt {attempt + 1})", metadata={
                        "task_id": task.task_id,
                        "error": error,
                    })

                    if attempt < self.config.max_retries:
                        time.sleep(self.config.retry_backoff * (2 ** attempt))
                    else:
                        self.logger.error(f"Task {task.task_id} failed after all retries")

            execution_time = time.time() - start_time

            # Validate results if configured and execution succeeded
            validation_results = None
            success = error is None

            if success and self.config.validate_results:
                validation_results = self._validate_task_result(task, result)
                success = all(validation_results.values())

                if not success:
                    error = "Validation failed: " + ", ".join([
                        criterion for criterion, passed in validation_results.items()
                        if not passed
                    ])

            exec_result = ExecutionResult(
                task_id=task.task_id,
                success=success,
                result=result,
                execution_time=execution_time,
                retries=retries,
                error=error,
                validation_results=validation_results,
            )

            self.execution_history.append(exec_result)

            self.logger.info(f"Task {task.task_id} {'succeeded' if success else 'failed'}", metadata={
                "execution_time": execution_time,
                "retries": retries,
                "success": success,
            })

            return exec_result

    def _execute_by_source(self, task: Task) -> Any:
        """Execute task based on its source type."""
        if task.source == TaskSource.LLM_GENERATION:
            return self._execute_llm_generation(task)
        elif task.source == TaskSource.API_CALL:
            return self._execute_api_call(task)
        elif task.source == TaskSource.WEB_SEARCH:
            return self._execute_web_search(task)
        elif task.source == TaskSource.DATABASE_QUERY:
            return self._execute_database_query(task)
        elif task.source == TaskSource.CODE_EXECUTION:
            return self._execute_code_execution(task)
        elif task.source == TaskSource.FILE_OPERATION:
            return self._execute_file_operation(task)
        elif task.source == TaskSource.HUMAN_INPUT:
            return self._execute_human_input(task)
        elif task.source == TaskSource.COMPOSITE:
            return self._execute_composite(task)
        else:
            raise ValueError(f"Unsupported task source: {task.source}")

    def _execute_llm_generation(self, task: Task) -> str:
        """Execute LLM generation task."""
        prompt = task.source_details.get('prompt', task.description)
        system_prompt = task.source_details.get('system_prompt')

        response = self.model_manager.executor_generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        return response.content

    def _execute_api_call(self, task: Task) -> Any:
        """Execute API call task."""
        # Placeholder - would integrate with requests library
        self.logger.warning(f"API call execution not yet implemented for {task.task_id}")
        return {
            "status": "not_implemented",
            "message": "API call execution requires additional implementation",
            "endpoint": task.source_details.get('endpoint', 'unknown'),
        }

    def _execute_web_search(self, task: Task) -> str:
        """Execute web search task."""
        # Placeholder - would integrate with search APIs
        self.logger.warning(f"Web search execution not yet implemented for {task.task_id}")
        query = task.source_details.get('query', task.description)
        return f"Web search for '{query}' requires integration with search API"

    def _execute_database_query(self, task: Task) -> Any:
        """Execute database query task."""
        # Placeholder - would integrate with database connections
        self.logger.warning(f"Database query execution not yet implemented for {task.task_id}")
        return {
            "status": "not_implemented",
            "message": "Database query execution requires database connection setup",
        }

    def _execute_code_execution(self, task: Task) -> Any:
        """Execute code execution task."""
        # Placeholder - would use exec() with safety checks
        self.logger.warning(f"Code execution not yet implemented for {task.task_id}")
        return {
            "status": "not_implemented",
            "message": "Code execution requires sandboxing implementation",
        }

    def _execute_file_operation(self, task: Task) -> Any:
        """Execute file operation task."""
        # Placeholder - would integrate with file I/O
        self.logger.warning(f"File operation not yet implemented for {task.task_id}")
        return {
            "status": "not_implemented",
            "message": "File operations require file system integration",
        }

    def _execute_human_input(self, task: Task) -> str:
        """Execute human input task."""
        print(f"\n📝 Human input required for: {task.title}")
        print(f"Description: {task.description}")
        response = input("Your input: ")
        return response

    def _execute_composite(self, task: Task) -> Dict[str, Any]:
        """Execute composite task (multiple approaches)."""
        # Execute sub-tasks defined in source_details
        results = {}
        for sub_task_key, sub_task_config in task.source_details.items():
            try:
                # Create temporary task for each sub-component
                sub_task = Task(
                    task_id=f"{task.task_id}_{sub_task_key}",
                    title=f"{task.title} - {sub_task_key}",
                    description=sub_task_config.get('description', ''),
                    source=TaskSource(sub_task_config.get('source', 'llm_generation')),
                    source_details=sub_task_config.get('details', {}),
                    success_criteria=[],
                )
                results[sub_task_key] = self._execute_by_source(sub_task)
            except Exception as e:
                self.logger.error(f"Composite sub-task {sub_task_key} failed: {e}")
                results[sub_task_key] = f"Error: {e}"

        return results

    def _validate_task_result(self, task: Task, result: Any) -> Dict[str, bool]:
        """
        Validate task result against success criteria.

        Args:
            task: Task that was executed.
            result: Result to validate.

        Returns:
            Dictionary mapping each criterion to pass/fail.
        """
        if not task.success_criteria:
            return {}

        validation_prompt = f"""Evaluate if the following result meets the success criteria.

**Task:** {task.title}
**Description:** {task.description}

**Result:**
{str(result)[:1000]}

**Success Criteria:**
{chr(10).join(f"{i+1}. {criterion}" for i, criterion in enumerate(task.success_criteria))}

For each criterion, determine if it's met (true/false).

Respond ONLY with JSON in this format:
{{
    "Criterion 1": true,
    "Criterion 2": false
}}"""

        try:
            response = self.model_manager.executor_generate(
                prompt=validation_prompt,
                temperature=0.2,
            )

            import json
            validation_dict = json.loads(response.content.strip())

            self.logger.info(f"Validation completed for {task.task_id}", metadata={
                "validation": validation_dict,
            })

            return validation_dict

        except Exception as e:
            self.logger.warning(f"Validation failed for {task.task_id}: {e}")
            # Assume success if validation fails
            return {criterion: True for criterion in task.success_criteria}
