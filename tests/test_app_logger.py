"""Tests for core.app_logger. Redirects the log directory into tmp_path."""

from __future__ import annotations

import logging
from pathlib import Path

import object_tracker.core.app_logger as app_logger


def _reset() -> None:
    logger = logging.getLogger(app_logger.LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_configure_logging_creates_handlers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(app_logger, "_log_dir", lambda: tmp_path)
    _reset()
    try:
        logger = app_logger.configure_logging("DEBUG")
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2  # file + console
        assert (tmp_path / "object_tracker.log").exists()
    finally:
        _reset()


def test_configure_logging_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(app_logger, "_log_dir", lambda: tmp_path)
    _reset()
    try:
        app_logger.configure_logging("INFO")
        handler_count = len(logging.getLogger(app_logger.LOGGER_NAME).handlers)
        logger = app_logger.configure_logging("WARNING")
        assert len(logger.handlers) == handler_count
        assert logger.level == logging.WARNING
    finally:
        _reset()


def test_configure_logging_without_console(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(app_logger, "_log_dir", lambda: tmp_path)
    _reset()
    try:
        logger = app_logger.configure_logging("INFO", console=False)
        assert len(logger.handlers) == 1
    finally:
        _reset()


def test_get_log_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(app_logger, "_log_dir", lambda: tmp_path)
    assert app_logger.get_log_path() == tmp_path / "object_tracker.log"
