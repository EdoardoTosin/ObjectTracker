"""Tests for core.camera probing helpers, using a stub in place of cv2.VideoCapture."""

from __future__ import annotations

import cv2

from object_tracker.core.camera import _CAP_DSHOW as CAP_DSHOW
from object_tracker.core.camera import _CAP_V4L2 as CAP_V4L2
from object_tracker.core.camera import (
    CameraStream,
    configure_capture,
    negotiate_capture_format,
    probe_resolution,
    probe_supported_fps,
    select_capture_backend,
)


class _FakeCapture:
    """Mimics enough of cv2.VideoCapture's .set/.get for probing logic.

    Accepts only *supported_resolutions* and, at the currently-set
    resolution, only *supported_fps*; everything else is rejected the way a
    real driver would reject an unsupported request. Every ``.set()`` call
    is also recorded in ``self.calls`` so tests can assert on properties
    (like FOURCC or buffer size) this stub doesn't otherwise model.
    """

    def __init__(self, supported_resolutions, supported_fps) -> None:
        self._supported_resolutions = set(supported_resolutions)
        self._supported_fps = set(supported_fps)
        self._width = 0
        self._height = 0
        self._fps = 0.0
        self.calls: list[tuple[int, object]] = []

    def set(self, prop, value) -> bool:
        self.calls.append((prop, value))
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            self._width = int(value)
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            self._height = int(value)
        elif prop == cv2.CAP_PROP_FPS:
            if (
                self._width,
                self._height,
            ) in self._supported_resolutions and value in self._supported_fps:
                self._fps = float(value)
            else:
                self._fps = 0.0
        return True

    def get(self, prop):
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return (
                self._width
                if (self._width, self._height) in self._supported_resolutions
                else 0
            )
        if prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return (
                self._height
                if (self._width, self._height) in self._supported_resolutions
                else 0
            )
        if prop == cv2.CAP_PROP_FPS:
            return self._fps
        return 0


# ── probe_resolution ──────────────────────────────────────────────────────────


def test_probe_resolution_accepted() -> None:
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps={30})
    assert probe_resolution(cap, 640, 480) is True


def test_probe_resolution_rejected() -> None:
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps={30})
    assert probe_resolution(cap, 1920, 1080) is False


# ── probe_supported_fps ───────────────────────────────────────────────────────


def test_probe_supported_fps_filters_to_driver_capability() -> None:
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps={30, 5})
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    supported = probe_supported_fps(cap, candidates=(30, 15, 5))
    assert supported == [30, 5]


def test_probe_supported_fps_empty_when_none_supported() -> None:
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps=set())
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    assert probe_supported_fps(cap, candidates=(30, 15, 5)) == []


# ── configure_capture ─────────────────────────────────────────────────────────


def test_configure_capture_picks_best_resolution() -> None:
    cap = _FakeCapture(
        supported_resolutions={(1280, 720), (640, 480)}, supported_fps={30}
    )
    info = configure_capture(cap, resolutions=((1920, 1080), (1280, 720), (640, 480)))
    assert (info.width, info.height) == (1280, 720)
    assert info.fps == 30


def test_configure_capture_falls_back_when_nothing_matches() -> None:
    cap = _FakeCapture(supported_resolutions=set(), supported_fps=set())
    info = configure_capture(cap, resolutions=((1920, 1080),))
    assert (info.width, info.height) == (320, 240)


def test_configure_capture_falls_back_fps_when_resolution_ok_but_no_fps() -> None:
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps=set())
    info = configure_capture(cap, resolutions=((640, 480),))
    assert (info.width, info.height) == (640, 480)
    assert info.fps == 10.0  # FALLBACK_FPS


# ── negotiate_capture_format ─────────────────────────────────────────────────


def test_negotiate_capture_format_sets_fourcc() -> None:
    cap = _FakeCapture(supported_resolutions=set(), supported_fps=set())
    negotiate_capture_format(cap, fourcc="MJPG", buffer_size=1)
    expected_fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    assert (cv2.CAP_PROP_FOURCC, expected_fourcc) in cap.calls


def test_negotiate_capture_format_sets_buffer_size() -> None:
    cap = _FakeCapture(supported_resolutions=set(), supported_fps=set())
    negotiate_capture_format(cap, fourcc="MJPG", buffer_size=1)
    assert (cv2.CAP_PROP_BUFFERSIZE, 1) in cap.calls


def test_negotiate_capture_format_respects_custom_buffer_size() -> None:
    cap = _FakeCapture(supported_resolutions=set(), supported_fps=set())
    negotiate_capture_format(cap, fourcc="YUYV", buffer_size=3)
    expected_fourcc = cv2.VideoWriter_fourcc(*"YUYV")
    assert (cv2.CAP_PROP_FOURCC, expected_fourcc) in cap.calls
    assert (cv2.CAP_PROP_BUFFERSIZE, 3) in cap.calls


def test_configure_capture_negotiates_format_before_returning() -> None:
    """configure_capture must request MJPEG/buffer size regardless of resolution outcome."""
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps={30})
    configure_capture(cap, resolutions=((640, 480),))
    expected_fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    assert (cv2.CAP_PROP_FOURCC, expected_fourcc) in cap.calls
    assert (cv2.CAP_PROP_BUFFERSIZE, 1) in cap.calls


def test_configure_capture_negotiates_format_even_on_fallback() -> None:
    cap = _FakeCapture(supported_resolutions=set(), supported_fps=set())
    configure_capture(cap, resolutions=((1920, 1080),))
    expected_fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    assert (cv2.CAP_PROP_FOURCC, expected_fourcc) in cap.calls


def test_negotiate_capture_format_runs_before_resolution_probing() -> None:
    """FOURCC must be requested first: some backends only unlock full FPS/resolution once it is."""
    cap = _FakeCapture(supported_resolutions={(640, 480)}, supported_fps={30})
    configure_capture(cap, resolutions=((640, 480),))
    fourcc_index = next(
        i for i, (prop, _) in enumerate(cap.calls) if prop == cv2.CAP_PROP_FOURCC
    )
    width_index = next(
        i for i, (prop, _) in enumerate(cap.calls) if prop == cv2.CAP_PROP_FRAME_WIDTH
    )
    assert fourcc_index < width_index


# ── select_capture_backend ────────────────────────────────────────────────────


def test_select_capture_backend_linux_prefers_v4l2() -> None:
    if CAP_V4L2 is None:
        return  # this OpenCV build has no V4L2 backend to prefer
    assert select_capture_backend("Linux") == CAP_V4L2


def test_select_capture_backend_windows_prefers_dshow() -> None:
    if CAP_DSHOW is None:
        return  # this OpenCV build has no DirectShow backend to prefer
    assert select_capture_backend("Windows") == CAP_DSHOW


def test_select_capture_backend_macos_uses_default() -> None:
    assert select_capture_backend("Darwin") is None


def test_select_capture_backend_unknown_platform_uses_default() -> None:
    assert select_capture_backend("SomeOtherOS") is None


# ── CameraStream ──────────────────────────────────────────────────────────────


def test_camera_stream_starts_unopened() -> None:
    stream = CameraStream(camera_index=2)
    assert stream.camera_index == 2
    assert stream.info is None
