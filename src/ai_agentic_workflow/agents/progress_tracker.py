"""
Progress Tracker for UI-ready state management.

Tracks workflow progress with status updates, timing, and
structured data ready for UI consumption.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from ..logging import get_logger


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CRITIQUING = "critiquing"


class WorkflowStage(str, Enum):
    """Workflow execution stages."""
    INITIALIZING = "initializing"
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    EXECUTING = "executing"
    CRITIQUING = "critiquing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskProgress:
    """Progress information for a single task."""
    task_id: str
    title: str
    description: str
    status: TaskStatus
    attempt_number: int = 1
    max_attempts: int = 3

    # Timing
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    # Output
    output: Optional[Any] = None
    error: Optional[str] = None

    # Critique results
    critique_score: Optional[float] = None
    critique_issues: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to UI-friendly dictionary."""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'attempt': f"{self.attempt_number}/{self.max_attempts}",
            'progress_percent': self._calculate_progress(),
            'elapsed_seconds': self.elapsed_time(),
            'output': str(self.output)[:200] if self.output else None,
            'error': self.error,
            'critique_score': self.critique_score,
            'critique_issues': self.critique_issues,
            'metadata': self.metadata,
        }

    def _calculate_progress(self) -> int:
        """Calculate progress percentage (0-100)."""
        if self.status == TaskStatus.PENDING:
            return 0
        elif self.status == TaskStatus.IN_PROGRESS:
            return 50
        elif self.status == TaskStatus.CRITIQUING:
            return 75
        elif self.status == TaskStatus.COMPLETED:
            return 100
        elif self.status == TaskStatus.FAILED:
            return 100
        elif self.status == TaskStatus.RETRYING:
            return int((self.attempt_number / self.max_attempts) * 100)
        return 0


@dataclass
class WorkflowProgress:
    """Overall workflow progress."""
    workflow_id: str
    user_query: str
    stage: WorkflowStage

    # Tasks
    tasks: List[TaskProgress] = field(default_factory=list)

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # Clarification
    clarification_rounds: int = 0
    pending_clarification: Optional[str] = None

    # Final output
    final_output: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: TaskProgress):
        """Add a task to track."""
        self.tasks.append(task)

    def update_task(self, task_id: str, **kwargs):
        """Update task progress."""
        for task in self.tasks:
            if task.task_id == task_id:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                break

    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """Get task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def completed_tasks(self) -> int:
        """Count completed tasks."""
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)

    def failed_tasks(self) -> int:
        """Count failed tasks."""
        return sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

    def elapsed_time(self) -> float:
        """Get total elapsed time in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def progress_percent(self) -> int:
        """Calculate overall progress percentage (0-100)."""
        if not self.tasks:
            return 0

        total_progress = sum(t._calculate_progress() for t in self.tasks)
        return int(total_progress / len(self.tasks))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to UI-friendly dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'user_query': self.user_query,
            'stage': self.stage.value,
            'progress_percent': self.progress_percent(),
            'elapsed_seconds': self.elapsed_time(),
            'tasks': {
                'total': len(self.tasks),
                'completed': self.completed_tasks(),
                'failed': self.failed_tasks(),
                'in_progress': sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS),
                'details': [t.to_dict() for t in self.tasks],
            },
            'clarification': {
                'rounds': self.clarification_rounds,
                'pending_question': self.pending_clarification,
            },
            'final_output': self.final_output,
            'timestamp': datetime.fromtimestamp(self.start_time).isoformat(),
            'metadata': self.metadata,
        }


class ProgressTracker:
    """
    Tracks and manages workflow progress for UI consumption.

    Provides real-time updates on task execution, critique cycles,
    and overall workflow state.
    """

    def __init__(self):
        """Initialize progress tracker."""
        self.workflows: Dict[str, WorkflowProgress] = {}
        self.logger = get_logger(__name__)

        self.logger.info("ProgressTracker initialized")

    def start_workflow(self, workflow_id: str, user_query: str) -> WorkflowProgress:
        """
        Start tracking a new workflow.

        Args:
            workflow_id: Unique workflow identifier.
            user_query: User's original query.

        Returns:
            WorkflowProgress instance.
        """
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            user_query=user_query,
            stage=WorkflowStage.INITIALIZING,
        )

        self.workflows[workflow_id] = progress

        self.logger.info(f"Started tracking workflow: {workflow_id}")

        return progress

    def update_stage(self, workflow_id: str, stage: WorkflowStage):
        """Update workflow stage."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].stage = stage
            self.logger.info(f"Workflow {workflow_id} stage: {stage.value}")

    def add_task(self, workflow_id: str, task: TaskProgress):
        """Add task to workflow."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].add_task(task)
            self.logger.info(f"Added task {task.task_id} to workflow {workflow_id}")

    def start_task(self, workflow_id: str, task_id: str):
        """Mark task as started."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.update_task(
                task_id,
                status=TaskStatus.IN_PROGRESS,
                start_time=time.time()
            )
            self.logger.info(f"Task {task_id} started")

    def complete_task(
        self,
        workflow_id: str,
        task_id: str,
        output: Any,
        critique_score: Optional[float] = None
    ):
        """Mark task as completed."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                end_time=time.time(),
                output=output,
                critique_score=critique_score
            )
            self.logger.info(f"Task {task_id} completed (score: {critique_score})")

    def fail_task(self, workflow_id: str, task_id: str, error: str):
        """Mark task as failed."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.update_task(
                task_id,
                status=TaskStatus.FAILED,
                end_time=time.time(),
                error=error
            )
            self.logger.error(f"Task {task_id} failed: {error}")

    def retry_task(self, workflow_id: str, task_id: str, attempt: int):
        """Mark task for retry."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.update_task(
                task_id,
                status=TaskStatus.RETRYING,
                attempt_number=attempt
            )
            self.logger.info(f"Task {task_id} retrying (attempt {attempt})")

    def critique_task(self, workflow_id: str, task_id: str):
        """Mark task as being critiqued."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.update_task(task_id, status=TaskStatus.CRITIQUING)
            self.logger.info(f"Task {task_id} being critiqued")

    def complete_workflow(
        self,
        workflow_id: str,
        final_output: str,
        success: bool = True
    ):
        """Complete workflow."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.stage = WorkflowStage.COMPLETED if success else WorkflowStage.FAILED
            workflow.final_output = final_output
            workflow.end_time = time.time()

            self.logger.info(f"Workflow {workflow_id} completed (success: {success})")

    def get_progress(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress as UI-friendly dict."""
        if workflow_id in self.workflows:
            return self.workflows[workflow_id].to_dict()
        return None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows progress."""
        return [w.to_dict() for w in self.workflows.values()]
