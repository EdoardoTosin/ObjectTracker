"""Tests for core.config: parse_objects, YAML loading, resolve_config, model discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from object_tracker.core.config import (
    discover_model_paths,
    load_yaml_config,
    parse_objects,
    resolve_config,
)

# ── parse_objects ─────────────────────────────────────────────────────────────


def test_parse_objects_all_keyword() -> None:
    assert parse_objects("all") is None


def test_parse_objects_case_insensitive_all() -> None:
    assert parse_objects("All") is None


def test_parse_objects_none_input() -> None:
    assert parse_objects(None) is None


def test_parse_objects_empty_string() -> None:
    assert parse_objects("") is None


def test_parse_objects_single() -> None:
    assert parse_objects("person") == frozenset({"person"})


def test_parse_objects_multiple_trims_whitespace() -> None:
    assert parse_objects("person, car,  traffic light") == frozenset(
        {"person", "car", "traffic light"}
    )


# ── load_yaml_config ──────────────────────────────────────────────────────────


def test_load_yaml_config_missing_file(tmp_path: Path) -> None:
    assert load_yaml_config(tmp_path / "missing.yaml") == {}


def test_load_yaml_config_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")
    assert load_yaml_config(path) == {}


def test_load_yaml_config_reads_values(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "recording_duration: 45\nobjects_to_detect: person\n", encoding="utf-8"
    )
    data = load_yaml_config(path)
    assert data["recording_duration"] == 45
    assert data["objects_to_detect"] == "person"


# ── resolve_config ────────────────────────────────────────────────────────────


def test_resolve_config_defaults_without_file(tmp_path: Path) -> None:
    cfg = resolve_config(config_path=tmp_path / "missing.yaml")
    assert cfg.camera_index == 0
    assert cfg.objects_to_detect is None
    assert cfg.dual_rate is False
    assert cfg.show_window is True


def test_resolve_config_yaml_values(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        "objects_to_detect: 'person, car'\nrecording_duration: 45\nbuffer_seconds: 5\n",
        encoding="utf-8",
    )
    cfg = resolve_config(config_path=yaml_path)
    assert cfg.objects_to_detect == frozenset({"person", "car"})
    assert cfg.recording_duration == 45
    assert cfg.buffer_seconds == 5


def test_resolve_config_cli_overrides_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("objects_to_detect: 'person'\n", encoding="utf-8")
    cfg = resolve_config(
        config_path=yaml_path, objects="car", camera_index=2, dual_rate=True
    )
    assert cfg.objects_to_detect == frozenset({"car"})
    assert cfg.camera_index == 2
    assert cfg.dual_rate is True


def test_resolve_config_explicit_paths(tmp_path: Path) -> None:
    models = tmp_path / "my_models"
    recordings = tmp_path / "my_recordings"
    cfg = resolve_config(
        config_path=tmp_path / "missing.yaml",
        models_dir=models,
        recordings_dir=recordings,
    )
    assert cfg.models_dir == models
    assert cfg.recordings_dir == recordings


# ── discover_model_paths ──────────────────────────────────────────────────────


def test_discover_model_paths_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        discover_model_paths(tmp_path / "nonexistent")


def test_discover_model_paths_missing_files(tmp_path: Path) -> None:
    (tmp_path / "classes.names").write_text("person\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        discover_model_paths(tmp_path)


def test_discover_model_paths_success(tmp_path: Path) -> None:
    (tmp_path / "classes.names").write_text("person\ncar\n", encoding="utf-8")
    (tmp_path / "model.pbtxt").write_text("", encoding="utf-8")
    (tmp_path / "weights.pb").write_bytes(b"")

    paths = discover_model_paths(tmp_path)
    assert paths.class_file.name == "classes.names"
    assert paths.config_file.name == "model.pbtxt"
    assert paths.weights_file.name == "weights.pb"


def test_discover_model_paths_real_models_dir() -> None:
    """The repository's bundled models/ directory must satisfy discovery."""
    from object_tracker.core.config import PROJECT_ROOT

    paths = discover_model_paths(PROJECT_ROOT / "models")
    assert paths.class_file.exists()
    assert paths.config_file.exists()
    assert paths.weights_file.exists()
