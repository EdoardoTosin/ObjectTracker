"""Tests for core.overlay.draw_hud."""

from __future__ import annotations

import numpy as np

from object_tracker.core.overlay import draw_hud


def _blank_frame() -> np.ndarray:
    return np.zeros((120, 320, 3), dtype=np.uint8)


def test_draw_hud_paints_pixels_with_no_detections() -> None:
    frame = _blank_frame()
    draw_hud(frame, [], now=1_700_000_000.0)
    assert frame.any()  # text was rendered onto the previously all-black frame


def test_draw_hud_with_detections_and_fps() -> None:
    frame = _blank_frame()
    draw_hud(frame, ["person", "car"], current_fps=27.3, now=1_700_000_000.0)
    assert frame.any()


def test_draw_hud_does_not_change_frame_shape() -> None:
    frame = _blank_frame()
    draw_hud(frame, ["person"], now=1_700_000_000.0)
    assert frame.shape == (120, 320, 3)
