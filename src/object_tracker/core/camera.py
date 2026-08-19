"""USB camera discovery, capability probing, and a thin capture wrapper.

The probing functions (:func:`probe_supported_fps`, :func:`probe_resolution`,
:func:`configure_capture`) only call ``.set``/``.get`` on the passed-in
capture object, so they work against any object with that interface,
including a lightweight test stub, without needing a real camera attached.
"""

from __future__ import annotations

import dataclasses
import logging
import platform

import cv2
import numpy as np

from object_tracker.core.constants import (
    CANDIDATE_FPS,
    COMMON_RESOLUTIONS,
    FALLBACK_FPS,
    FALLBACK_RESOLUTION,
    FPS_TOLERANCE,
    PREFERRED_BUFFER_SIZE,
    PREFERRED_FOURCC,
)

logger = logging.getLogger(__name__)

_CAP_V4L2: int | None
try:
    _CAP_V4L2 = cv2.CAP_V4L2
except AttributeError:  # pragma: no cover: only missing on non-Linux builds
    _CAP_V4L2 = None

_CAP_DSHOW: int | None
try:
    _CAP_DSHOW = cv2.CAP_DSHOW
except AttributeError:  # pragma: no cover: only missing on non-Windows builds
    _CAP_DSHOW = None


@dataclasses.dataclass(frozen=True)
class CameraInfo:
    """Resolution and frame rate a camera was successfully configured for."""

    width: int
    height: int
    fps: float


def probe_supported_fps(
    cap: cv2.VideoCapture, candidates: tuple[float, ...] = CANDIDATE_FPS
) -> list[float]:
    """Return the subset of *candidates* the driver actually honours.

    A candidate is accepted only when the driver's reported FPS after
    ``cap.set`` is within :data:`FPS_TOLERANCE` of the requested value.
    Drivers that just echo back whatever was requested fail this check for
    unsupported rates, giving an accurate capability list instead of a list
    of wishes.
    """
    supported: set[float] = set()
    for candidate in candidates:
        cap.set(cv2.CAP_PROP_FPS, candidate)
        reported = cap.get(cv2.CAP_PROP_FPS)
        if (
            reported > 0
            and abs(reported - candidate) / max(candidate, 1) < FPS_TOLERANCE
        ):
            supported.add(reported)
    return sorted(supported, reverse=True)


def probe_resolution(cap: cv2.VideoCapture, width: int, height: int) -> bool:
    """Request *width* x *height* and return True if the driver accepted it exactly."""
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    actual = (
        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    return actual == (width, height)


def negotiate_capture_format(
    cap: cv2.VideoCapture,
    fourcc: str = PREFERRED_FOURCC,
    buffer_size: int = PREFERRED_BUFFER_SIZE,
) -> None:
    """Request *fourcc* and a minimal internal buffer before resolution probing.

    Both are best-effort and safe to call against any backend: a camera or
    backend that ignores either ``.set`` call keeps working with its own
    defaults, just potentially at a lower resolution/FPS ceiling or with
    extra read latency under a long exposure.
    """
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))  # type: ignore[attr-defined]
    cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)


def configure_capture(
    cap: cv2.VideoCapture, resolutions: tuple[tuple[int, int], ...] = COMMON_RESOLUTIONS
) -> CameraInfo:
    """Configure *cap* at the highest supported resolution and best matching FPS.

    Falls back to :data:`FALLBACK_RESOLUTION` / :data:`FALLBACK_FPS` if none
    of *resolutions* are accepted by the driver.
    """
    negotiate_capture_format(cap)

    for width, height in resolutions:
        if not probe_resolution(cap, width, height):
            continue
        supported_fps = probe_supported_fps(cap)
        fps = supported_fps[0] if supported_fps else FALLBACK_FPS
        cap.set(cv2.CAP_PROP_FPS, fps)
        logger.info(
            "Camera configured: %dx%d @ %.2f FPS (supported: %s)",
            width,
            height,
            fps,
            supported_fps,
        )
        return CameraInfo(width=width, height=height, fps=fps)

    width, height = FALLBACK_RESOLUTION
    logger.warning(
        "No probed resolution accepted; falling back to %dx%d @ %.1f FPS",
        width,
        height,
        FALLBACK_FPS,
    )
    return CameraInfo(width=width, height=height, fps=FALLBACK_FPS)


def select_capture_backend(system: str) -> int | None:
    """Pick the most reliable OpenCV capture backend for *system*.

    V4L2 on Linux and DirectShow on Windows are both substantially more
    reliable than OpenCV's own platform defaults (GStreamer autodetection
    and Media Foundation respectively) for UVC webcams, which commonly fail
    to negotiate MJPEG or hang on certain formats under the default
    backend. Returns ``None`` (use OpenCV's default) on any other platform,
    or if the preferred backend isn't available in this OpenCV build.
    """
    if system == "Linux" and _CAP_V4L2 is not None:
        return _CAP_V4L2
    if system == "Windows" and _CAP_DSHOW is not None:
        return _CAP_DSHOW
    return None


def _open_capture(
    camera_index: int,
) -> cv2.VideoCapture:  # pragma: no cover: needs hardware
    """Open *camera_index* on the most reliable backend for the current platform."""
    backend = select_capture_backend(platform.system())
    if backend is None:
        return cv2.VideoCapture(camera_index)
    return cv2.VideoCapture(camera_index, backend)


class CameraStream:
    """Owns a ``cv2.VideoCapture`` device: opening, probing, reading, and reconnecting."""

    def __init__(self, camera_index: int) -> None:
        self.camera_index = camera_index
        self.info: CameraInfo | None = None
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> CameraInfo:  # pragma: no cover: needs hardware
        """Open the camera and probe it for the best supported resolution/FPS.

        Raises:
            RuntimeError: The camera device could not be opened.
        """
        cap = _open_capture(self.camera_index)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Cannot open camera at index {self.camera_index}")

        self.info = configure_capture(cap)
        self._cap = cap
        return self.info

    def read(
        self,
    ) -> tuple[bool, np.ndarray | None]:  # pragma: no cover: needs hardware
        """Read the next frame. Returns ``(False, None)`` if not open or the read fails."""
        if self._cap is None:
            return False, None
        return self._cap.read()

    def release(self) -> None:  # pragma: no cover: needs hardware
        """Release the underlying capture device, if open."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def reconnect(self) -> CameraInfo:  # pragma: no cover: needs hardware
        """Release and reopen the camera. Raises RuntimeError on failure."""
        self.release()
        return self.open()
