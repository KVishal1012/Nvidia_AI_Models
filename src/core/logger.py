"""
logger.py

Centralized logging configuration for the Chennai Flood GeoAI project.

Features:
- Logs messages to the terminal.
- Writes logs to a rotating file.
- Prevents duplicate handlers.
- Uses one consistent format across all project modules.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import LOGS_DIR


DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE = LOGS_DIR / "geoai_pipeline.log"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Path | None = DEFAULT_LOG_FILE,
) -> logging.Logger:
    """
    Create or return a configured logger.

    Parameters
    ----------
    name:
        Logger name. Usually pass ``__name__``.

    level:
        Logging level, such as logging.INFO or logging.DEBUG.

    log_file:
        Path to the log file. Pass None to disable file logging.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid adding duplicate handlers when the module is imported again.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger