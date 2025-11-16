"""
Structured logging with context propagation and trace integration.

Provides rich, contextual logging with automatic trace ID injection,
structured metadata, and multiple output formats.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from .trace_manager import get_current_trace_id


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs with trace information.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add trace ID if available
        trace_id = get_current_trace_id()
        if trace_id:
            log_data['trace_id'] = trace_id

        # Add any extra fields from the record
        if hasattr(record, 'metadata'):
            log_data['metadata'] = record.metadata

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StructuredLogger:
    """
    Enhanced logger with structured output and trace integration.

    Provides rich logging capabilities with automatic trace ID propagation,
    structured metadata, and contextual information.
    """

    def __init__(self, name: str, level: int = logging.INFO, structured: bool = True):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__).
            level: Logging level (default: INFO).
            structured: If True, use JSON structured output. If False, use standard format.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.structured = structured

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Set formatter based on structured flag
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _log(self, level: int, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal logging method with metadata support."""
        extra = {}
        if metadata:
            extra['metadata'] = metadata

        # Add trace ID info to message if not structured
        if not self.structured:
            trace_id = get_current_trace_id()
            if trace_id:
                message = f"[trace:{trace_id[:8]}] {message}"

        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with optional metadata."""
        self._log(logging.DEBUG, message, metadata, **kwargs)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with optional metadata."""
        self._log(logging.INFO, message, metadata, **kwargs)

    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with optional metadata."""
        self._log(logging.WARNING, message, metadata, **kwargs)

    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs):
        """Log error message with optional metadata and exception info."""
        if exc_info:
            kwargs['exc_info'] = True
        self._log(logging.ERROR, message, metadata, **kwargs)

    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs):
        """Log critical message with optional metadata and exception info."""
        if exc_info:
            kwargs['exc_info'] = True
        self._log(logging.CRITICAL, message, metadata, **kwargs)

    def exception(self, message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Log exception with full traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, metadata, **kwargs)


# Cache for logger instances
_logger_cache: Dict[str, StructuredLogger] = {}


def get_logger(
    name: str,
    level: int = logging.INFO,
    structured: bool = False
) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name (typically __name__).
        level: Logging level.
        structured: If True, use JSON structured output.

    Returns:
        StructuredLogger instance.
    """
    cache_key = f"{name}_{level}_{structured}"
    if cache_key not in _logger_cache:
        _logger_cache[cache_key] = StructuredLogger(name, level, structured)
    return _logger_cache[cache_key]


def setup_logging(level: int = logging.INFO, structured: bool = False):
    """
    Configure root logger for the application.

    Args:
        level: Logging level for all loggers.
        structured: If True, use JSON structured output.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
