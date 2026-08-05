"""Structured logging setup for Hermes Social Agent per Section 40 of the guide."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter for structured observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Extra structured fields per Section 40
        structured_keys = [
            "pipeline_run_id",
            "topic_id",
            "post_id",
            "model_route",
            "stage",
            "duration",
            "retry",
            "result",
            "error",
        ]
        for key in structured_keys:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleReadableFormatter(logging.Formatter):
    """Human-readable console formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        base_msg = super().format(record)
        extras = []
        structured_keys = [
            "pipeline_run_id",
            "topic_id",
            "post_id",
            "model_route",
            "stage",
            "duration",
            "retry",
            "result",
            "error",
        ]
        for key in structured_keys:
            if hasattr(record, key):
                val = getattr(record, key)
                extras.append(f"{key}={val}")
        if extras:
            return f"{base_msg} | " + " ".join(extras)
        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_console: bool = False,
) -> logging.Logger:
    """Initialize structured application logging."""
    logger = logging.getLogger("hermes_social")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_console:
        console_handler.setFormatter(StructuredJsonFormatter())
    else:
        console_handler.setFormatter(
            ConsoleReadableFormatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False
    return logger
