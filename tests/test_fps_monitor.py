"""Tests for core.fps_monitor: FrameRateMonitor and CameraMode classification."""

from __future__ import annotations

import pytest

from object_tracker.core.fps_monitor import CameraMode, FrameRateMonitor, classify_fps

# ── classify_fps ──────────────────────────────────────────────────────────────


def test_classify_fps_normal_mode() -> None:
    assert classify_fps(30.0) is CameraMode.NORMAL


def test_classify_fps_night_mode() -> None:
    assert classify_fps(4.5) is CameraMode.NIGHT


def test_classify_fps_boundary_is_normal() -> None:
    from object_tracker.core.constants import NIGHT_MODE_THRESHOLD_FPS

    assert classify_fps(NIGHT_MODE_THRESHOLD_FPS) is CameraMode.NORMAL


# ── FrameRateMonitor ─────────────────────────────────────────────────────────


def test_monitor_single_sample_no_update() -> None:
    monitor = FrameRateMonitor(window_size=5)
    monitor.update(0.0)
    assert monitor.current_fps == monitor.stable_fps


def test_monitor_tracks_normal_rate() -> None:
    monitor = FrameRateMonitor(window_size=10)
    for i in range(11):
        monitor.update(i / 30.0)
    assert 29.0 < monitor.current_fps < 31.0
    assert monitor.mode is CameraMode.NORMAL


def test_monitor_tracks_night_rate() -> None:
    monitor = FrameRateMonitor(window_size=10)
    for i in range(11):
        monitor.update(i / 5.0)
    assert 4.5 < monitor.current_fps < 5.5
    assert monitor.mode is CameraMode.NIGHT


def test_monitor_stable_fps_only_updates_after_full_window() -> None:
    monitor = FrameRateMonitor(window_size=5, initial_fps=30.0)
    # Feed 3 samples (4 timestamps) at a much slower rate; window not full yet.
    for i in range(4):
        monitor.update(i / 5.0)
    assert monitor.stable_fps == 30.0
    assert monitor.current_fps != 30.0


def test_monitor_clamps_extreme_fps() -> None:
    monitor = FrameRateMonitor(window_size=3)
    monitor.update(0.0)
    monitor.update(0.0001)  # near-zero delta -> huge instantaneous fps
    from object_tracker.core.constants import MAX_FPS

    assert monitor.current_fps <= MAX_FPS


def test_monitor_ignores_non_positive_delta() -> None:
    monitor = FrameRateMonitor(window_size=5, initial_fps=15.0)
    monitor.update(1.0)
    monitor.update(1.0)  # duplicate timestamp -> zero delta, ignored
    assert monitor.current_fps == 15.0


def test_monitor_reacts_to_a_single_long_exposure_stall() -> None:
    """A single multi-second gap (long auto-exposure) must immediately read as night mode.

    The implied instantaneous rate (1/3 fps) is below MIN_FPS, so it clamps
    to MIN_FPS rather than reporting a fractional value; either way it must
    still classify as night mode.
    """
    from object_tracker.core.constants import MIN_FPS

    monitor = FrameRateMonitor(window_size=10, initial_fps=30.0)
    monitor.update(0.0)
    monitor.update(3.0)  # a single frame that took 3s to arrive
    assert monitor.current_fps == pytest.approx(MIN_FPS)
    assert monitor.mode is CameraMode.NIGHT


def test_monitor_recovers_after_stall_when_normal_rate_resumes() -> None:
    """current_fps must climb back to normal once the camera exits its long-exposure stall."""
    monitor = FrameRateMonitor(window_size=5, initial_fps=30.0)
    monitor.update(0.0)
    monitor.update(3.0)  # one slow (night-mode-like) frame
    assert monitor.mode is CameraMode.NIGHT
    for i in range(1, 6):
        monitor.update(3.0 + i / 30.0)  # frames resume at a normal 30 fps
    assert monitor.mode is CameraMode.NORMAL
    assert 29.0 < monitor.current_fps < 31.0


def test_monitor_stable_fps_unaffected_by_a_single_stall_within_a_full_window() -> None:
    """One slow frame inside an otherwise-normal window must not crash stable_fps to zero."""
    monitor = FrameRateMonitor(window_size=5, initial_fps=30.0)
    timestamps = [0.0, 1 / 30, 2 / 30, 2.0, 2.0 + 1 / 30, 2.0 + 2 / 30]
    for t in timestamps:
        monitor.update(t)
    assert monitor.stable_fps > 0
