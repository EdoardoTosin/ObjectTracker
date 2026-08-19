"""Tests for core.timing."""

from __future__ import annotations

from object_tracker.core.constants import MAX_BUFFER_FRAMES, MIN_BUFFER_FRAMES
from object_tracker.core.timing import compute_buffer_frames, should_stop_recording

# ── compute_buffer_frames ────────────────────────────────────────────────────


def test_compute_buffer_frames_normal_rate() -> None:
    assert compute_buffer_frames(30.0, 10) == 300


def test_compute_buffer_frames_clamps_to_minimum() -> None:
    """A very slow night-mode camera must still buffer at least MIN_BUFFER_FRAMES."""
    assert compute_buffer_frames(2.0, 10) == MIN_BUFFER_FRAMES


def test_compute_buffer_frames_clamps_to_maximum() -> None:
    assert compute_buffer_frames(120.0, 10) == MAX_BUFFER_FRAMES


# ── should_stop_recording ────────────────────────────────────────────────────


def test_should_stop_recording_before_duration() -> None:
    assert (
        should_stop_recording(
            last_detection_time=0.0, current_time=10.0, recording_duration=30
        )
        is False
    )


def test_should_stop_recording_after_duration() -> None:
    assert (
        should_stop_recording(
            last_detection_time=0.0, current_time=31.0, recording_duration=30
        )
        is True
    )


def test_should_stop_recording_exactly_at_duration() -> None:
    assert (
        should_stop_recording(
            last_detection_time=0.0, current_time=30.0, recording_duration=30
        )
        is False
    )
