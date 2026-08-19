"""Application logging setup: console output plus a rotating file log."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "object_tracker"


def _log_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "ObjectTracker" / "logs"


def get_log_path() -> Path:
    """Return the path of the rotating log file."""
    return _log_dir() / "object_tracker.log"


def configure_logging(level: str = "INFO", *, console: bool = True) -> logging.Logger:
    """Attach handlers to the root application logger and set its level.

    Safe to call more than once: handlers are attached only on the first
    call, later calls just update the level. Child loggers created with
    ``logging.getLogger(__name__)`` throughout the package propagate here.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        log_dir = _log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_dir / "object_tracker.log"),
            maxBytes=1_048_576,
            backupCount=4,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if console:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger
