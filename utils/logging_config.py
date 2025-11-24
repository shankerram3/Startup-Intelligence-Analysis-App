"""
Structured Logging Configuration for GraphRAG System
Provides centralized logging setup with JSON formatting and contextual information
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.typing import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application-wide context to all log entries"""
    event_dict["app"] = "startup-intelligence"
    event_dict["version"] = "1.0.0"
    return event_dict


def setup_logging(
    log_level: str = "INFO", json_logs: bool = True, log_file: Optional[Path] = None
) -> None:
    """
    Configure structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON formatted logs; otherwise human-readable
        log_file: Optional path to write logs to file
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Shared processors for all configurations
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    # Choose renderer based on configuration
    if json_logs:
        # Production: JSON logs for parsing
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable colored output
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # If log file specified, add file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))

        # JSON format for file logs
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
        file_handler.setFormatter(formatter)

        # Add to root logger
        logging.root.addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("processing_started", article_id=123, phase="extraction")
        logger.error("extraction_failed", error=str(e), article_id=123, exc_info=True)
    """
    return structlog.get_logger(name)


def log_function_call(logger: structlog.stdlib.BoundLogger, func_name: str, **kwargs):
    """
    Log function call with parameters

    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger.debug("function_call", function=func_name, **kwargs)


def log_performance(
    logger: structlog.stdlib.BoundLogger, operation: str, duration_ms: float, **context
):
    """
    Log performance metrics

    Args:
        logger: Logger instance
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        **context: Additional context
    """
    logger.info(
        "performance_metric", operation=operation, duration_ms=duration_ms, **context
    )


def log_api_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
    **context,
):
    """
    Log API request with standard fields

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        request_id: Optional request ID for tracing
        **context: Additional context
    """
    log_level = (
        "info" if status_code < 400 else "warning" if status_code < 500 else "error"
    )

    getattr(logger, log_level)(
        "api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        request_id=request_id,
        **context,
    )


# Example usage patterns for different scenarios
EXAMPLE_USAGE = """
# Basic logging
logger = get_logger(__name__)
logger.info("server_started", host="0.0.0.0", port=8000)

# With context
logger.info("article_scraped", url=url, word_count=len(content))

# Error logging with exception
try:
    process_article(article)
except Exception as e:
    logger.error(
        "article_processing_failed",
        article_id=article.id,
        error=str(e),
        exc_info=True  # Includes full traceback
    )

# Performance logging
import time
start = time.time()
result = expensive_operation()
duration_ms = (time.time() - start) * 1000
log_performance(logger, "expensive_operation", duration_ms, result_count=len(result))

# API request logging
log_api_request(
    logger,
    method="POST",
    path="/api/query",
    status_code=200,
    duration_ms=234.5,
    request_id="req-123",
    user_id="user-456"
)
"""
