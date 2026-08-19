"""Application configuration: YAML defaults merged with explicit overrides.

Public surface
--------------
:class:`AppConfig`: frozen dataclass with the fully resolved settings.
:class:`ModelPaths`: resolved .names/.pbtxt/.pb file paths.
:func:`resolve_config`: merge config.yaml with explicit overrides.
:func:`discover_model_paths`: locate the SSD model files in a directory.
:func:`parse_objects`: parse the objects_to_detect CLI/YAML value.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml

from object_tracker.core.constants import (
    DEFAULT_BUFFER_SECONDS,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_NMS_THRESHOLD,
    DEFAULT_OBJECTS_TO_DETECT,
    DEFAULT_RECONNECT_INTERVAL,
    DEFAULT_RECORDING_DURATION,
)

# src/object_tracker/core/config.py -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MODELS_DIR = PROJECT_ROOT / "models"
DEFAULT_RECORDINGS_DIR = PROJECT_ROOT / "recordings"
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config.yaml"


# ── Model file discovery ─────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class ModelPaths:
    """Resolved paths to the three files an OpenCV DNN SSD model needs."""

    class_file: Path
    config_file: Path
    weights_file: Path


def discover_model_paths(models_dir: Path) -> ModelPaths:
    """Locate the ``.names`` / ``.pbtxt`` / ``.pb`` files inside *models_dir*.

    Raises:
        FileNotFoundError: *models_dir* doesn't exist, or any file is missing.
    """
    models_dir = Path(models_dir)
    if not models_dir.is_dir():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")

    found: dict[str, Path] = {}
    suffix_map = {
        ".names": "class_file",
        ".pbtxt": "config_file",
        ".pb": "weights_file",
    }
    for path in sorted(models_dir.iterdir()):
        field = suffix_map.get(path.suffix.lower())
        if field and field not in found:
            found[field] = path

    missing = [suffix for suffix, field in suffix_map.items() if field not in found]
    if missing:
        raise FileNotFoundError(
            f"Missing required model file(s) with extension(s) {missing} in {models_dir}"
        )

    return ModelPaths(**found)  # type: ignore[arg-type]


# ── Settings ─────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class AppConfig:
    """Fully resolved runtime configuration for a tracker run."""

    camera_index: int = DEFAULT_CAMERA_INDEX
    objects_to_detect: frozenset[str] | None = None  # None -> detect all classes
    show_window: bool = True
    dual_rate: bool = False
    recording_duration: float = DEFAULT_RECORDING_DURATION
    buffer_seconds: int = DEFAULT_BUFFER_SECONDS
    reconnect_interval: float = DEFAULT_RECONNECT_INTERVAL
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    nms_threshold: float = DEFAULT_NMS_THRESHOLD
    models_dir: Path = DEFAULT_MODELS_DIR
    recordings_dir: Path = DEFAULT_RECORDINGS_DIR
    log_level: str = "INFO"


def parse_objects(raw: str | None) -> frozenset[str] | None:
    """Parse a comma-separated object list.

    Returns ``None`` (meaning "detect every class") for ``'all'`` or empty
    input; otherwise a frozenset of the trimmed, comma-separated names.
    """
    if not raw or raw.strip().lower() == "all":
        return None
    return frozenset(item.strip() for item in raw.split(",") if item.strip())


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load a YAML config file, returning an empty dict if it does not exist."""
    path = Path(path)
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def resolve_config(
    *,
    config_path: Path = DEFAULT_CONFIG_FILE,
    camera_index: int | None = None,
    objects: str | None = None,
    show_window: bool | None = None,
    dual_rate: bool | None = None,
    log_level: str | None = None,
    models_dir: Path | None = None,
    recordings_dir: Path | None = None,
) -> AppConfig:
    """Merge *config_path*'s YAML with explicit overrides into an :class:`AppConfig`.

    Any override left as ``None`` falls back to the YAML value, and finally
    to the built-in default.
    """
    raw = load_yaml_config(config_path)

    resolved_objects = (
        objects
        if objects is not None
        else raw.get("objects_to_detect", DEFAULT_OBJECTS_TO_DETECT)
    )

    return AppConfig(
        camera_index=camera_index if camera_index is not None else DEFAULT_CAMERA_INDEX,
        objects_to_detect=parse_objects(resolved_objects),
        show_window=show_window if show_window is not None else True,
        dual_rate=dual_rate if dual_rate is not None else False,
        recording_duration=raw.get("recording_duration", DEFAULT_RECORDING_DURATION),
        buffer_seconds=raw.get("buffer_seconds", DEFAULT_BUFFER_SECONDS),
        reconnect_interval=raw.get("reconnect_interval", DEFAULT_RECONNECT_INTERVAL),
        confidence_threshold=raw.get(
            "confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD
        ),
        nms_threshold=raw.get("nms_threshold", DEFAULT_NMS_THRESHOLD),
        models_dir=(
            Path(models_dir)
            if models_dir is not None
            else Path(raw.get("models_dir", DEFAULT_MODELS_DIR))
        ),
        recordings_dir=(
            Path(recordings_dir)
            if recordings_dir is not None
            else Path(raw.get("recordings_folder", DEFAULT_RECORDINGS_DIR))
        ),
        log_level=log_level if log_level is not None else raw.get("log_level", "INFO"),
    )
