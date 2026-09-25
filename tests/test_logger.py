"""Tests for structured logger setup."""

import json

from loguru import logger

from src.utils.logger import setup_logger


def test_setup_logger_creates_file(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logger(level="INFO", log_file=str(log_file), structured=False, run_id="test_run")
    logger.info("Hello from test")
    logger.complete()
    assert log_file.exists()
    content = log_file.read_text()
    assert "Hello from test" in content
    assert "test_run" in content


def test_setup_logger_structured_mode(tmp_path):
    log_file = tmp_path / "structured.log"
    setup_logger(level="DEBUG", log_file=str(log_file), structured=True, run_id="json_run")
    logger.info("Structured message")
    logger.complete()
    line = log_file.read_text(encoding="utf-8").strip().splitlines()[0]
    payload = json.loads(line)
    assert payload["record"]["message"] == "Structured message"
    assert payload["record"]["extra"]["run_id"] == "json_run"
