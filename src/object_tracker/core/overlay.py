"""HUD overlay: timestamp, detection summary, and live FPS text on a frame."""

from __future__ import annotations

import time

import cv2
import numpy as np

_TIMESTAMP_COLOR = (0, 255, 255)
_DETECTION_COLOR = (0, 255, 0)
_FPS_COLOR = (255, 255, 0)


def draw_hud(
    frame: np.ndarray,
    detected_names: list[str],
    *,
    current_fps: float | None = None,
    now: float | None = None,
) -> None:
    """Draw a timestamp, detection summary, and optional FPS readout onto *frame* in place."""
    timestamp = time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime(now))
    cv2.putText(
        frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, _TIMESTAMP_COLOR, 2
    )

    detected_info = (
        f"Detected: {', '.join(detected_names)}"
        if detected_names
        else "No objects detected"
    )
    cv2.putText(
        frame,
        detected_info,
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        _DETECTION_COLOR,
        2,
    )

    if current_fps is not None:
        cv2.putText(
            frame,
            f"FPS: {current_fps:.1f}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            _FPS_COLOR,
            2,
        )
