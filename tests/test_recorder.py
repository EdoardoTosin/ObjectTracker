"""Tests for core.recorder: VideoRecorder start/write/stop and FPS adaptation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from object_tracker.core.recorder import VideoRecorder

WIDTH, HEIGHT = 64, 48


def _frame() -> np.ndarray:
    return np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)


# ── start/write/stop ──────────────────────────────────────────────────────────


def test_start_recording_creates_file(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.start_recording()
    try:
        assert recorder.is_recording is True
        assert list(tmp_path.glob("detection_*.mp4"))
    finally:
        recorder.stop_recording()


def test_write_frame_increments_count(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.start_recording()
    t = 1_000.0
    for i in range(5):
        recorder.write_frame(_frame(), t + i / 30.0)
    stats = recorder.stats()
    recorder.stop_recording()
    assert stats.frames_written == 5


def test_write_frame_noop_when_not_recording(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.write_frame(_frame())  # must not raise
    assert recorder.stats().active is False


def test_stop_recording_releases_writer(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.start_recording()
    recorder.stop_recording()
    assert recorder.is_recording is False
    recorder.stop_recording()  # calling again must be a safe no-op


def test_write_frame_duplicates_on_large_gap(tmp_path: Path) -> None:
    """A frame gap much larger than 1/fps should insert duplicate frames."""
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 10.0)
    recorder.start_recording()
    recorder.write_frame(_frame(), 0.0)
    recorder.write_frame(_frame(), 1.0)  # 1s gap at 10fps -> ~9 duplicates expected
    frames = recorder.stats().frames_written
    recorder.stop_recording()
    assert frames > 2


def test_write_frame_gap_clamped_regardless_of_real_stall_duration(
    tmp_path: Path,
) -> None:
    """A long auto-exposure stall (night mode) must not write unbounded duplicates.

    MAX_FRAME_GAP_SECONDS clamps the gap used for duplication math to 2.0s
    no matter how long the real-world stall was, so a single very slow
    frame (a multi-minute IR-cut exposure, a resumed-after-reconnect frame)
    always produces exactly MAX_FRAME_GAP_SECONDS worth of frames, not a
    burst proportional to the actual elapsed time.
    """
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.start_recording()
    recorder.write_frame(_frame(), 0.0)
    recorder.write_frame(_frame(), 120.0)  # a 2-minute stall, far beyond the 2s clamp
    frames = recorder.stats().frames_written
    recorder.stop_recording()
    # 1 initial frame + 59 duplicates spanning the clamped 2.0s gap + 1 arriving frame:
    # 61 frames spaced at 1/30s apart span exactly 2.0s, regardless of the real 120s gap.
    assert frames == 61


def test_write_frame_ignores_frames_faster_than_max_fps(tmp_path: Path) -> None:
    """Two frames closer together than 1/MAX_FPS must not both be written."""
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    recorder.start_recording()
    recorder.write_frame(_frame(), 0.0)
    recorder.write_frame(
        _frame(), 0.0001
    )  # far faster than any real camera can deliver
    frames = recorder.stats().frames_written
    recorder.stop_recording()
    assert frames == 1


# ── adapt_fps ─────────────────────────────────────────────────────────────────


def test_adapt_fps_disabled_without_dual_rate(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0, dual_rate=False)
    assert recorder.adapt_fps(5.0) is False
    assert recorder.target_fps == 30.0


def test_adapt_fps_applies_large_change(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0, dual_rate=True)
    assert recorder.adapt_fps(5.0) is True
    assert recorder.target_fps == 5.0


def test_adapt_fps_ignores_small_change(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0, dual_rate=True)
    assert recorder.adapt_fps(31.0) is False
    assert recorder.target_fps == 30.0


def test_start_recording_uses_target_fps_in_dual_rate(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0, dual_rate=True)
    recorder.adapt_fps(5.0)
    recorder.start_recording()
    stats = recorder.stats()
    recorder.stop_recording()
    assert stats.recording_fps == 5.0


# ── stats() when idle ─────────────────────────────────────────────────────────


def test_stats_inactive_by_default(tmp_path: Path) -> None:
    recorder = VideoRecorder(tmp_path, WIDTH, HEIGHT, 30.0)
    stats = recorder.stats()
    assert stats.active is False
    assert stats.frames_written == 0
