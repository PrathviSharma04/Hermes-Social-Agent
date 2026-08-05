"""Tests for structured logging setup and JSON serialization."""

import json
import logging
from pathlib import Path

from hermes_social.logging_setup import setup_logging


def test_setup_logging_console_only() -> None:
    """Test initializing logger with console handler only."""
    logger = setup_logging(log_level="DEBUG", json_console=False)
    assert logger.name == "hermes_social"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert logger.propagate is False


def test_structured_json_file_logging(tmp_path: Path) -> None:
    """Test writing structured logs with custom extra fields to JSON log file."""
    log_file = tmp_path / "test_structured.log"
    logger = setup_logging(log_level="INFO", log_file=log_file)

    logger.info(
        "Test pipeline run",
        extra={
            "pipeline_run_id": "run_101",
            "topic_id": 42,
            "stage": "RESEARCH",
            "duration": 1.25,
            "result": "SUCCESS",
        },
    )

    # Flush handlers to ensure file write
    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8").strip()
    log_data = json.loads(content)

    assert log_data["level"] == "INFO"
    assert log_data["message"] == "Test pipeline run"
    assert log_data["pipeline_run_id"] == "run_101"
    assert log_data["topic_id"] == 42
    assert log_data["stage"] == "RESEARCH"
    assert log_data["duration"] == 1.25
    assert log_data["result"] == "SUCCESS"
