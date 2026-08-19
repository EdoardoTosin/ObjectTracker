# Development Guide

Canonical instructions for developing, testing, and understanding ObjectTracker's architecture.

## Prerequisites

- Python ≥ 3.9
- [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/EdoardoTosin/ObjectTracker.git
cd ObjectTracker
uv sync --all-groups
```

`--all-groups` installs the dev dependencies (ruff, black, mypy, pytest, pytest-cov, types-PyYAML) alongside the runtime ones.

## Architecture

```
src/object_tracker/
  __init__.py           Package version (__version__), read by hatchling at
                         build time via [tool.hatch.version] in pyproject.toml.
  __main__.py            Entry point: `uv run object-tracker` resolves here via
                         [project.scripts] in pyproject.toml, dispatching to cli.app().
  cli.py                  Typer + Rich CLI: parses flags, resolves an AppConfig,
                         and calls core.tracker.run_tracker().
  core/
    app_logger.py          Console + rotating file logger, configured once from
                         cli.py before any other module logs anything.
    camera.py                USB camera discovery: resolution/FPS probing,
                         MJPEG/buffer-size negotiation, backend selection
                         (V4L2 on Linux, DirectShow on Windows), and the
                         CameraStream open/read/release/reconnect wrapper.
    config.py                 config.yaml and CLI merging into a frozen
                         AppConfig, plus model file (.names/.pbtxt/.pb) discovery.
    constants.py                All tunable defaults and thresholds in one place.
    detector.py                  OpenCV DNN object detection (ObjectDetector,
                         Detection) and bounding-box rendering (draw_detections)
                         as two separate functions, so detection logic can be
                         tested without a frame ever being mutated.
    fps_monitor.py                 Live frame-rate estimation from real frame
                         timestamps, not the driver's reported value, plus
                         normal/night mode classification.
    overlay.py                      Timestamp/detection/FPS HUD text drawn onto
                         the preview frame.
    recorder.py                      Event-triggered recording: frame-timing
                         synchronization (duplicate-frame insertion) and
                         FPS-change handling for dual-rate cameras.
    timing.py                         Pure buffer-size and stop-recording
                         calculations, split out for independent testing.
    tracker.py                         Main loop tying the camera, detector,
                         recorder, and overlay together; owns signal handling
                         and reconnection.
tests/                                  pytest + pytest-cov, covering every
                         module above except cli.py, __main__.py, and
                         tracker.py; see "Testing" below.
models/                                  Bundled MobileNet SSD v3 weights,
                         graph config, and COCO class names, loaded directly
                         with no separate download step.
```

## Testing

```bash
uv run pytest
```

Runs with coverage enabled (`pytest-cov`) and fails below 85% (`[tool.pytest.ini_options]` / `[tool.coverage.*]` in `pyproject.toml`).

- `cli.py`, `__main__.py`, and `core/tracker.py` are excluded from the coverage gate: they need a real camera or a terminal to exercise meaningfully.
- `core/camera.py`'s hardware-touching methods (`CameraStream.open`/`read`/`release`/`reconnect`) carry `# pragma: no cover` for the same reason. The pure probing and format-negotiation functions in that file (`probe_resolution`, `probe_supported_fps`, `configure_capture`, `negotiate_capture_format`, `select_capture_backend`) are still fully unit-tested against a stub capture object.
- `tests/test_detector.py` loads the real model files from `models/` rather than mocking OpenCV's DNN module, so the actual inference path is exercised on every run.

> [!IMPORTANT]
> After changing any hardware-facing code (`core/camera.py`, `core/recorder.py`, `core/tracker.py`), run `uv run object-tracker --no-window` against a real camera and confirm detection, recording, and reconnection still work. Automated tests cover the pure logic; they cannot exercise an actual UVC device.

## Development Commands

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run black src/ tests/

# Type-check
uv run mypy src/

# Test
uv run pytest
```

## Where the Version Lives

`src/object_tracker/__init__.py`'s `__version__` is the only place the version is stored. `[tool.hatch.version]` in `pyproject.toml` reads it from there for packaging; never hand-edit a version anywhere else.

## Credits

- [OpenCV](https://opencv.org/): detection, video I/O, and rendering.
- Pre-trained [MobileNet SSD](../models/) model and COCO class list.
- [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/) for the CLI.
- Logo by [Vectors Tank on Flaticon](https://www.flaticon.com/free-icon/objet_14702720).
