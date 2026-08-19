"""Pure timing and sizing calculations used by the tracker loop and recorder."""

from __future__ import annotations

from object_tracker.core.constants import MAX_BUFFER_FRAMES, MIN_BUFFER_FRAMES


def compute_buffer_frames(fps: float, seconds: float) -> int:
    """Return how many frames to keep in the pre-detection ring buffer.

    Clamped to ``[MIN_BUFFER_FRAMES, MAX_BUFFER_FRAMES]`` so very low
    (night mode) or very high frame rates both produce a sane buffer size.
    """
    return max(MIN_BUFFER_FRAMES, min(int(fps * seconds), MAX_BUFFER_FRAMES))


def should_stop_recording(
    last_detection_time: float, current_time: float, recording_duration: float
) -> bool:
    """Return True once *recording_duration* seconds have elapsed with no detection."""
    return (current_time - last_detection_time) > recording_duration
