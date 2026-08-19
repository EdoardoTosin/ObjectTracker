"""Rolling frame-rate estimation and day/night mode classification.

Handles USB cameras that switch between a normal daytime rate (commonly
~30 fps) and a much slower night/IR mode (commonly ~4-5 fps): the monitor
tracks the live frame rate from actual frame timestamps rather than trusting
the driver's reported FPS, since many drivers don't update it on a mode
switch.
"""

from __future__ import annotations

import collections
from enum import Enum

from object_tracker.core.constants import (
    FPS_WINDOW_SIZE,
    MAX_FPS,
    MIN_FPS,
    NIGHT_MODE_THRESHOLD_FPS,
    NORMAL_MODE_FPS,
)


class CameraMode(str, Enum):
    """Classification of the camera's currently observed frame rate."""

    NORMAL = "normal"
    NIGHT = "night"


def classify_fps(fps: float) -> CameraMode:
    """Classify a measured FPS as normal (~30 fps) or night (~4-5 fps) mode."""
    return CameraMode.NIGHT if fps < NIGHT_MODE_THRESHOLD_FPS else CameraMode.NORMAL


def _clamp_fps(fps: float) -> float:
    return max(MIN_FPS, min(MAX_FPS, fps))


class FrameRateMonitor:
    """Tracks the live frame rate of a variable-rate (dual day/night) camera.

    Frame timestamps feed a rolling window average. ``current_fps`` reacts
    immediately to new samples so mode changes are detected quickly;
    ``stable_fps`` only updates once a full window has been collected,
    giving a settled estimate that's safe to restart a recording at.
    """

    def __init__(
        self, window_size: int = FPS_WINDOW_SIZE, initial_fps: float = NORMAL_MODE_FPS
    ) -> None:
        self.window_size = window_size
        self._frame_times: collections.deque[float] = collections.deque(
            maxlen=window_size
        )
        self.current_fps = _clamp_fps(initial_fps)
        self.stable_fps = self.current_fps

    def update(self, frame_time: float) -> None:
        """Record a new frame timestamp and recompute the current FPS estimate."""
        self._frame_times.append(frame_time)
        if len(self._frame_times) < 2:
            return

        deltas = [
            self._frame_times[i] - self._frame_times[i - 1]
            for i in range(1, len(self._frame_times))
        ]
        avg_delta = sum(deltas) / len(deltas)
        if avg_delta <= 0:
            return

        self.current_fps = _clamp_fps(1.0 / avg_delta)
        if len(self._frame_times) >= self.window_size:
            self.stable_fps = self.current_fps

    @property
    def mode(self) -> CameraMode:
        """Current camera mode inferred from the live FPS estimate."""
        return classify_fps(self.current_fps)
