"""Structured logging configuration with optional JSON output."""

from loguru import logger
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    level: str = "INFO",
    log_file: str = "logs/trading_system.log",
    structured: bool = False,
    run_id: Optional[str] = None,
):
    """
    Configure loguru logger with console + file sinks.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path for the rotating log file
        structured: If True, emit JSON-serialized logs (machine-parseable)
        run_id: Optional run identifier injected into every log record
    """
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.remove()  # remove default handler

    def _add_run_id(record):
        record["extra"]["run_id"] = run_id or "local"
        return True

    # Console sink
    if structured:
        logger.add(
            sys.stderr,
            level=level,
            serialize=True,  # JSON lines
            filter=_add_run_id,
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True,
            filter=_add_run_id,
        )

    # File sink (always structured-friendly + rotation)
    logger.add(
        log_file,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[run_id]} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        filter=_add_run_id,
    )

    return logger
