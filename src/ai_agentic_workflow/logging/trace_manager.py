"""
Trace manager for end-to-end request tracing and correlation.

Provides trace IDs, span tracking, and context propagation for debugging
complex multi-step workflows.
"""

import uuid
import time
import contextvars
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json

# Context variable for trace ID propagation across async boundaries
_trace_context = contextvars.ContextVar('trace_context', default=None)


@dataclass
class Span:
    """Represents a single operation span within a trace."""
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    parent_span_id: Optional[str] = None

    def duration_ms(self) -> Optional[float]:
        """Calculate span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization."""
        return {
            'span_id': self.span_id,
            'name': self.name,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms(),
            'metadata': self.metadata,
            'error': self.error,
            'parent_span_id': self.parent_span_id,
        }


@dataclass
class Trace:
    """Represents a complete trace with multiple spans."""
    trace_id: str
    start_time: float
    end_time: Optional[float] = None
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span):
        """Add a span to this trace."""
        self.spans.append(span)

    def duration_ms(self) -> Optional[float]:
        """Calculate total trace duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization."""
        return {
            'trace_id': self.trace_id,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms(),
            'metadata': self.metadata,
            'spans': [span.to_dict() for span in self.spans],
            'total_spans': len(self.spans),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert trace to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class TraceManager:
    """
    Manages distributed tracing for agentic workflows.

    Provides functionality to create traces, spans, and propagate
    context across function boundaries for comprehensive debugging.
    """

    def __init__(self):
        self._active_traces: Dict[str, Trace] = {}
        self._current_span_stack: List[str] = []

    def start_trace(self, trace_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace.

        Args:
            trace_id: Optional trace ID. If not provided, generates a UUID.
            metadata: Optional metadata to attach to the trace.

        Returns:
            The trace ID.
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        trace = Trace(
            trace_id=trace_id,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self._active_traces[trace_id] = trace
        _trace_context.set(trace_id)

        return trace_id

    def end_trace(self, trace_id: str):
        """End a trace and mark its end time."""
        if trace_id in self._active_traces:
            self._active_traces[trace_id].end_time = time.time()

    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None
    ) -> str:
        """
        Start a new span within a trace.

        Args:
            name: Name of the operation/span.
            trace_id: Trace ID. If not provided, uses current context.
            metadata: Optional metadata for the span.
            parent_span_id: Optional parent span ID for nested spans.

        Returns:
            The span ID.
        """
        if trace_id is None:
            trace_id = _trace_context.get()

        if trace_id not in self._active_traces:
            # Auto-create trace if not exists
            self.start_trace(trace_id)

        span_id = str(uuid.uuid4())
        span = Span(
            span_id=span_id,
            name=name,
            start_time=time.time(),
            metadata=metadata or {},
            parent_span_id=parent_span_id or (self._current_span_stack[-1] if self._current_span_stack else None)
        )

        self._active_traces[trace_id].add_span(span)
        self._current_span_stack.append(span_id)

        return span_id

    def end_span(self, span_id: str, error: Optional[str] = None):
        """
        End a span and mark its completion.

        Args:
            span_id: The span ID to end.
            error: Optional error message if the span failed.
        """
        # Find the span across all traces
        for trace in self._active_traces.values():
            for span in trace.spans:
                if span.span_id == span_id:
                    span.end_time = time.time()
                    if error:
                        span.error = error

                    # Remove from stack
                    if span_id in self._current_span_stack:
                        self._current_span_stack.remove(span_id)
                    return

    def add_span_metadata(self, span_id: str, key: str, value: Any):
        """Add metadata to a specific span."""
        for trace in self._active_traces.values():
            for span in trace.spans:
                if span.span_id == span_id:
                    span.metadata[key] = value
                    return

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._active_traces.get(trace_id)

    def get_current_trace_id(self) -> Optional[str]:
        """Get the current trace ID from context."""
        return _trace_context.get()

    def export_trace(self, trace_id: str) -> Optional[str]:
        """Export a trace as JSON."""
        trace = self.get_trace(trace_id)
        if trace:
            return trace.to_json()
        return None

    def clear_trace(self, trace_id: str):
        """Remove a trace from active traces."""
        if trace_id in self._active_traces:
            del self._active_traces[trace_id]


# Global trace manager instance
_global_trace_manager = TraceManager()


def get_trace_manager() -> TraceManager:
    """Get the global trace manager instance."""
    return _global_trace_manager


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID from context."""
    return _trace_context.get()


class trace_context:
    """
    Context manager for automatic trace and span management.

    Example:
        with trace_context("my_operation", metadata={"key": "value"}) as span_id:
            # Your code here
            pass
    """

    def __init__(
        self,
        name: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_trace: bool = False
    ):
        self.name = name
        self.trace_id = trace_id
        self.metadata = metadata
        self.is_trace = is_trace
        self.span_id = None
        self.manager = get_trace_manager()

    def __enter__(self) -> str:
        if self.is_trace:
            self.trace_id = self.manager.start_trace(self.trace_id, self.metadata)
            return self.trace_id
        else:
            self.span_id = self.manager.start_span(self.name, self.trace_id, self.metadata)
            return self.span_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_msg = f"{exc_type.__name__}: {exc_val}"
            if self.span_id:
                self.manager.end_span(self.span_id, error=error_msg)
        else:
            if self.span_id:
                self.manager.end_span(self.span_id)

        if self.is_trace and self.trace_id:
            self.manager.end_trace(self.trace_id)

        return False  # Don't suppress exceptions
