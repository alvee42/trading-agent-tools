"""
Logging configuration for the Weather Agent.

Provides structured logging to console and optionally to file.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    debug: bool = False
):
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        debug: If True, override level to DEBUG
    """
    # Override level if debug flag set
    if debug:
        level = "DEBUG"

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    # Console handler (stderr to keep stdout clean for JSON output)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # File handler if specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        file_handler.setFormatter(formatter)

        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Capture all levels, handlers will filter
        handlers=handlers,
        force=True  # Override any existing configuration
    )

    # Reduce noise from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured: level={level}, file={log_file}")
