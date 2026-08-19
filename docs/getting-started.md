# Getting Started

## Requirements

| Requirement | Minimum version |
|---|---|
| Python | 3.9 |
| uv (package manager) | any recent version |
| Operating system | Windows, macOS, or Linux (Raspberry Pi OS included) |
| Camera | Any USB camera exposed via V4L2 (Linux) or DirectShow (Windows) |

## Installation

```bash
git clone https://github.com/EdoardoTosin/ObjectTracker.git
cd ObjectTracker
uv sync
```

This creates an isolated virtual environment under `.venv/` and installs OpenCV, NumPy, PyYAML, Typer, and Rich. The MobileNet SSD model files are already bundled in [`models/`](../models/), with no separate download step.

On a headless machine (no display attached), replace the GUI-capable OpenCV build with the headless one and always pass `--no-window`:

```bash
uv remove opencv-python
uv add opencv-python-headless
```

## Running Your First Session

```bash
uv run object-tracker
```

With no flags, ObjectTracker:

1. Opens camera index `0` and probes it for the highest resolution/FPS combination it supports.
2. Loads the object list from [`config.yaml`](../config.yaml) (defaults to `person, car, traffic light`).
3. Opens a live preview window and starts logging to the console.
4. Starts recording to `recordings/<YYYY-MM-DD>/` the moment a matching object appears, and stops after 30 seconds with no further detections.

Press **`q`** or **`Esc`** in the preview window, or **Ctrl+C** in the terminal, to stop.

### Checking the version

```bash
uv run object-tracker --version
```

## Choosing a Camera

If you have more than one camera attached, list devices with your OS's tools (e.g. `v4l2-ctl --list-devices` on Linux, or check Device Manager on Windows) and pass the index:

```bash
uv run object-tracker --camera-index 1
```

ObjectTracker probes each of `3840x2160`, `1920x1080`, `1280x720`, and `640x480` in order and uses the highest one the driver actually accepts, along with the fastest FPS the driver honours at that resolution. If none of those resolutions are accepted, it falls back to `320x240 @ 10 fps`.

## Dual-Rate (Day/Night) Cameras

Some USB cameras switch to a slower frame rate under low light or IR/night mode, commonly dropping from ~30 fps to ~4-5 fps. Without special handling, a fixed-rate recorder either plays night-mode footage back in fast-forward or desyncs entirely.

Pass `--dual-rate` to enable adaptation:

```bash
uv run object-tracker --dual-rate
```

In this mode, ObjectTracker measures the *actual* delivered frame rate (not just what the driver reports) using a rolling window, classifies it as **normal** (≥ 12 fps) or **night** (< 12 fps) mode, and:

- Duplicates frames as needed so already-open recordings play back at the correct real-time speed even while the rate is drifting.
- Cleanly restarts the recording at the new target rate once the change is confirmed stable, rather than continuing with a mismatched file header.

See [Configuration](configuration.md) for the underlying thresholds.

## Application Data

### Recordings

Video files are written to `recordings/<YYYY-MM-DD>/detection_<HH-MM-SS>_<width>x<height>_<fps>fps.mp4`, created automatically on first use. Override the location with `--recordings-dir` or the `recordings_folder` key in `config.yaml`.

### Logs

A rolling log (up to 5 x 1 MB files) is written alongside console output:

| OS | Location |
|---|---|
| Windows | `%APPDATA%\ObjectTracker\logs\object_tracker.log` |
| macOS / Linux | `~/.local/share/ObjectTracker/logs/object_tracker.log` |
