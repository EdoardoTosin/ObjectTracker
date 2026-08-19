"""Shared constants used across all modules."""

from __future__ import annotations

# ── Camera probing ──────────────────────────────────────────────────────────

#: Resolutions probed in descending order of preference.
COMMON_RESOLUTIONS: tuple[tuple[int, int], ...] = (
    (3840, 2160),  # 4K UHD
    (1920, 1080),  # Full HD
    (1280, 720),  # HD
    (640, 480),  # VGA
)

#: Frame rates probed against each resolution, descending. Includes the
#: night-mode range (4-5 fps) alongside standard rates so dual-rate cameras
#: are fully characterized regardless of which mode they power on in.
CANDIDATE_FPS: tuple[float, ...] = (120, 60, 30, 29.97, 25, 24, 15, 10, 6, 5, 4)

#: Relative tolerance for accepting a driver-reported FPS as genuinely
#: supported (vs. drivers that just echo back whatever value was requested).
FPS_TOLERANCE: float = 0.1

#: FOURCC requested before resolution/FPS probing. Most UVC webcams,
#: including IR-cut day/night security modules, only reach their full
#: resolution/FPS combinations in MJPEG; the uncompressed format some
#: backends default to doesn't fit 1080p30 in USB2.0's bandwidth, silently
#: capping the camera to a lower resolution or a crawl of a few FPS.
PREFERRED_FOURCC: str = "MJPG"

#: Requested capture buffer size, in frames. A camera under long
#: auto-exposure (typical of IR-cut night mode) takes far longer than one
#: nominal frame interval to produce a frame; a larger internal buffer
#: means a blocking read can return a stale, already-queued frame instead
#: of the newest one. Best-effort: backends that ignore this keep working,
#: just with extra latency.
PREFERRED_BUFFER_SIZE: int = 1

#: Fallback resolution/FPS used when the camera rejects every probed mode.
FALLBACK_RESOLUTION: tuple[int, int] = (320, 240)
FALLBACK_FPS: float = 10.0

# ── Dual-rate day/night camera modes ────────────────────────────────────────

#: Nominal daytime frame rate for cameras that drop rate under IR/night mode.
NORMAL_MODE_FPS: float = 30.0

#: Nominal night-mode frame rate range for dual-rate USB cameras.
NIGHT_MODE_FPS_RANGE: tuple[float, float] = (4.0, 5.0)

#: Below this measured FPS the stream is classified as night mode. Placed
#: well above the night range's ceiling and well below normal mode so a few
#: dropped or duplicated frames can't flip the classification back and forth.
NIGHT_MODE_THRESHOLD_FPS: float = 12.0

#: Minimum absolute FPS delta before the recorder adopts a new target rate.
FPS_ADAPTATION_THRESHOLD: float = 2.0

#: Clamp bounds applied to any measured or adapted FPS value.
MIN_FPS: float = 1.0
MAX_FPS: float = 120.0

# ── Frame rate monitor ──────────────────────────────────────────────────────

#: Rolling window size (frames) used to estimate the live frame rate.
FPS_WINDOW_SIZE: int = 30

# ── Recording ────────────────────────────────────────────────────────────────

#: Seconds to keep recording after the last detection.
DEFAULT_RECORDING_DURATION: float = 30.0

#: Seconds of pre-detection frames to keep buffered so a recording's first
#: file includes the moments leading up to the triggering detection.
DEFAULT_BUFFER_SECONDS: int = 10
MIN_BUFFER_FRAMES: int = 30
MAX_BUFFER_FRAMES: int = 300

#: Seconds between camera reconnection attempts after repeated read failures.
DEFAULT_RECONNECT_INTERVAL: float = 5.0

#: Consecutive failed frame reads before a reconnection attempt is made.
MAX_FAILED_CAPTURES: int = 10

#: Video codecs tried in order; the first that opens a real file is used.
CODEC_FALLBACKS: tuple[str, ...] = ("mp4v", "XVID", "MJPG", "X264")

#: Cap on how large a single frame-timing gap is treated as, in seconds,
#: before duplicate-frame math is applied (guards against runaway padding
#: after a long stall, e.g. a reconnect).
MAX_FRAME_GAP_SECONDS: float = 2.0

#: Cap on how much duplicated playback time a single gap can insert.
MAX_DUPLICATE_SECONDS: float = 3.0

# ── Detection ────────────────────────────────────────────────────────────────

DEFAULT_OBJECTS_TO_DETECT: str = "all"
DETECTOR_INPUT_SIZE: tuple[int, int] = (320, 320)
DETECTOR_INPUT_SCALE: float = 1.0 / 127.5
DETECTOR_INPUT_MEAN: tuple[float, float, float] = (127.5, 127.5, 127.5)
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.45
DEFAULT_NMS_THRESHOLD: float = 0.2

# ── Camera device ────────────────────────────────────────────────────────────

DEFAULT_CAMERA_INDEX: int = 0
