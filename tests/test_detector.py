"""Tests for core.detector, exercised against the repository's bundled SSD model."""

from __future__ import annotations

import numpy as np
import pytest

from object_tracker.core.config import PROJECT_ROOT, discover_model_paths
from object_tracker.core.detector import ObjectDetector, load_class_names

MODELS_DIR = PROJECT_ROOT / "models"


@pytest.fixture(scope="module")
def model_paths():
    return discover_model_paths(MODELS_DIR)


def test_load_class_names(model_paths) -> None:
    names = load_class_names(model_paths.class_file)
    assert "person" in names
    assert "car" in names


def test_detector_defaults_to_all_classes(model_paths) -> None:
    detector = ObjectDetector(model_paths)
    assert detector.objects_to_detect == frozenset(detector.class_names)


def test_detector_restricts_to_requested_classes(model_paths) -> None:
    detector = ObjectDetector(model_paths, objects_to_detect=frozenset({"person"}))
    assert detector.objects_to_detect == frozenset({"person"})


def test_detect_on_blank_frame_returns_no_detections(model_paths) -> None:
    detector = ObjectDetector(model_paths)
    frame = np.zeros((320, 320, 3), dtype=np.uint8)
    assert detector.detect(frame) == []
