"""Event-triggered video recording with frame-timing synchronization.

Handles cameras that switch frame rates between day and night modes by
duplicating frames to keep played-back video at the correct real-time speed,
and by exposing when the recorder should be restarted so a rate change never
desyncs a file that's already open. OpenCV's ``VideoWriter`` cannot change
FPS mid-stream, so a rate change only takes effect on the *next* recording.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from object_tracker.core.constants import (
    CODEC_FALLBACKS,
    FPS_ADAPTATION_THRESHOLD,
    MAX_DUPLICATE_SECONDS,
    MAX_FPS,
    MAX_FRAME_GAP_SECONDS,
    MIN_FPS,
)

logger = logging.getLogger(__name__)

_MIN_FRAME_INTERVAL = 1.0 / MAX_FPS


@dataclasses.dataclass
class RecordingStats:
    """Snapshot of the currently active recording, if any."""

    active: bool
    frames_written: int = 0
    duration: float = 0.0
    average_fps: float = 0.0
    recording_fps: float | None = None


def probe_working_codec(
    output_dir: Path,
    width: int,
    height: int,
    fps: float,
    codecs: tuple[str, ...] = CODEC_FALLBACKS,
) -> str:
    """Return the first codec in *codecs* that can actually open a ``VideoWriter``."""
    probe_path = Path(output_dir) / "._codec_probe.mp4"
    try:
        for codec in codecs:
            writer = cv2.VideoWriter(
                str(probe_path),
                cv2.VideoWriter_fourcc(*codec),  # type: ignore[attr-defined]
                fps,
                (width, height),
            )
            opened = writer.isOpened()
            writer.release()
            if opened:
                return codec
        return codecs[0]
    finally:
        probe_path.unlink(missing_ok=True)


class VideoRecorder:
    """Starts/stops timestamped recordings and writes frames with timing sync.

    Thread-safe: an internal ``RLock`` guards all mutable state so
    ``start_recording`` may safely trigger a buffer flush via
    :meth:`write_frame` without deadlocking.
    """

    def __init__(
        self,
        output_dir: Path,
        width: int,
        height: int,
        fps: float,
        *,
        dual_rate: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self.fps = fps
        self.dual_rate = dual_rate
        self.target_fps = fps

        self._writer: cv2.VideoWriter | None = None
        self._lock = threading.RLock()
        self._recording = False
        self._start_time: float | None = None
        self._last_frame_time: float | None = None
        self._frames_written = 0
        self._recording_fps: float | None = None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._codec = probe_working_codec(self.output_dir, width, height, fps)

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording and self._writer is not None

    def adapt_fps(self, new_fps: float) -> bool:
        """Update the target FPS to use for the *next* recording.

        Requires ``dual_rate=True``. Returns True if the change was large
        enough to apply. If a recording is currently active, the caller must
        call :meth:`stop_recording` for the new rate to take effect.
        """
        if not self.dual_rate:
            return False

        with self._lock:
            new_fps = max(MIN_FPS, min(MAX_FPS, new_fps))
            if abs(new_fps - self.target_fps) <= FPS_ADAPTATION_THRESHOLD:
                return False
            logger.info("Target FPS changed: %.1f -> %.1f", self.target_fps, new_fps)
            if self._recording:
                logger.warning(
                    "FPS changed mid-recording; stop_recording() must be called "
                    "before the new rate takes effect."
                )
            self.target_fps = new_fps
            return True

    def start_recording(self) -> None:
        """Open a new timestamped output file and begin accepting frames.

        Raises:
            OSError: The ``VideoWriter`` could not be opened.
        """
        with self._lock:
            recording_fps = self.target_fps if self.dual_rate else self.fps
            filename = (
                f"detection_{datetime.now():%H-%M-%S}_"
                f"{self.width}x{self.height}_{int(recording_fps)}fps.mp4"
            )
            output_path = self.output_dir / filename

            fourcc = cv2.VideoWriter_fourcc(*self._codec)  # type: ignore[attr-defined]
            writer = cv2.VideoWriter(
                str(output_path), fourcc, recording_fps, (self.width, self.height)
            )
            if not writer.isOpened():
                writer.release()
                raise OSError(f"Failed to open video file for writing: {output_path}")

            self._writer = writer
            self._recording = True
            self._recording_fps = recording_fps
            self._start_time = time.time()
            self._last_frame_time = None
            self._frames_written = 0
            logger.info("Recording started: %s at %.2f FPS", output_path, recording_fps)

    def write_frame(self, frame: np.ndarray, frame_time: float | None = None) -> None:
        """Write *frame*, duplicating frames as needed to preserve real-time playback speed.

        *frame_time* should be the frame's original capture timestamp
        (``time.time()``-based). Duplication math is based on the FPS the
        current file was opened with, not ``target_fps``, so a mid-session
        adaptation can never desync an already-open recording.
        """
        if frame_time is None:
            frame_time = time.time()

        with self._lock:
            if not self._recording or self._writer is None:
                return

            if self._last_frame_time is not None:
                gap = min(frame_time - self._last_frame_time, MAX_FRAME_GAP_SECONDS)
                if gap < _MIN_FRAME_INTERVAL:
                    return

                writer_fps = self._recording_fps or self.fps
                expected_interval = 1.0 / writer_fps
                if gap > expected_interval * 1.5:
                    duplicates = max(
                        0,
                        min(
                            int(round(gap / expected_interval)) - 1,
                            int(writer_fps * MAX_DUPLICATE_SECONDS),
                        ),
                    )
                    for _ in range(duplicates):
                        self._writer.write(frame)
                        self._frames_written += 1

            self._writer.write(frame)
            self._frames_written += 1
            self._last_frame_time = frame_time

    def stop_recording(self) -> None:
        """Finalize and release the current output file, if any."""
        with self._lock:
            if not self._recording or self._writer is None:
                return
            duration = time.time() - self._start_time if self._start_time else 0.0
            avg_fps = self._frames_written / duration if duration > 0 else 0.0
            logger.info(
                "Recording stopped: %d frames in %.2fs (avg %.2f FPS)",
                self._frames_written,
                duration,
                avg_fps,
            )
            self._writer.release()
            self._writer = None
            self._recording = False
            self._start_time = None
            self._last_frame_time = None
            self._recording_fps = None

    def stats(self) -> RecordingStats:
        """Return a snapshot of the current recording state."""
        with self._lock:
            if not self._recording or self._start_time is None:
                return RecordingStats(active=False)
            duration = time.time() - self._start_time
            avg_fps = self._frames_written / duration if duration > 0 else 0.0
            return RecordingStats(
                active=True,
                frames_written=self._frames_written,
                duration=duration,
                average_fps=avg_fps,
                recording_fps=self._recording_fps,
            )

    def release(self) -> None:
        """Stop any active recording. Safe to call multiple times."""
        self.stop_recording()
