# Troubleshooting

## Camera

### "Cannot open camera at index N"

**Cause:** No camera is attached at that index, it's in use by another application, or the OS lacks permission to access it.

**Actions:**
- Confirm the device exists: `v4l2-ctl --list-devices` (Linux) or check Device Manager (Windows).
- Close any other application using the camera (browsers, video call software).
- On Linux, ensure your user is in the `video` group: `sudo usermod -aG video $USER` (re-login required).
- Try `--camera-index 1`, `2`, etc.

### The camera opens but at a much lower resolution/FPS than expected

**Cause:** The driver rejected every resolution ObjectTracker probed (`3840x2160`, `1920x1080`, `1280x720`, `640x480`), falling back to `320x240 @ 10 fps`.

**Action:** Check the startup log line `Camera configured: ...` (or the fallback warning). Some drivers only report accurate capabilities after being opened with a specific backend; on Linux this is usually V4L2 (used automatically). If the fallback keeps triggering, the camera may only expose non-standard resolutions; open an issue with your camera's `v4l2-ctl --list-formats-ext` output.

### "Frame capture failed" repeating, then reconnection attempts

**Cause:** The camera stopped delivering frames: a loose USB connection, a driver crash, or the device was unplugged.

**Action:** This is expected recovery behavior: after `MAX_FAILED_CAPTURES` (10) consecutive failures, ObjectTracker releases and reopens the device, waiting `reconnect_interval` seconds between attempts. If reconnection keeps failing, check the physical connection and try a different USB port (avoid unpowered hubs for cameras that draw significant current).

## Dual-Rate / Night Mode

### Recordings play back too fast or too slow after a day/night switch

**Cause:** `--dual-rate` was not enabled, so ObjectTracker assumed a fixed rate for the whole session.

**Action:** Re-run with `--dual-rate`. See [Getting Started](getting-started.md#dual-rate-daynight-cameras).

### With `--dual-rate` on, the camera mode flips back and forth rapidly

**Cause:** The live FPS estimate is hovering close to `NIGHT_MODE_THRESHOLD_FPS` (12.0), which can happen with cameras whose night mode runs faster than ~4-5 fps, or under inconsistent lighting.

**Action:** See [Configuration: Dual-Rate Thresholds](configuration.md#dual-rate-thresholds) to adjust `NIGHT_MODE_THRESHOLD_FPS` and `FPS_ADAPTATION_THRESHOLD` for your camera's actual rates.

### A recording restarts mid-session and splits into two files

**Cause:** This is intentional. OpenCV's `VideoWriter` cannot change FPS mid-file, so when `--dual-rate` detects a confirmed rate change, ObjectTracker stops the current recording and starts a new one at the new rate on the next detection, rather than writing a file with an incorrect header.

## Detection

### "Unknown object class(es): [...]" at startup

**Cause:** `--objects` (or `objects_to_detect` in `config.yaml`) contains a name that doesn't appear in `models/coco.names`.

**Action:** Check spelling and casing against `models/coco.names`, or use `--objects all` to detect every class.

### Nothing is ever detected

**Actions:**
- Confirm the object is actually in frame and reasonably well-lit; the model is not designed for full darkness without a night-mode-capable camera.
- Lower `confidence_threshold` in `config.yaml` (e.g. `0.3`) to see if borderline detections start appearing, then tune back up.
- Verify the class name is correct: `--objects all` detects everything, which helps isolate a naming/config issue from a model/lighting issue.

### Detections flicker on and off for an object that's clearly still there

**Cause:** Per-frame confidence naturally fluctuates near the threshold, especially at low resolutions or in poor lighting.

**Action:** This does not affect recording continuity: as long as detections resume within `recording_duration` seconds, the same recording continues. Lower `confidence_threshold` slightly if the gaps are frequent enough to cause premature stop/start cycles.

## Recording

### No video files appear under `recordings/`

**Actions:**
- Check the log for `Failed to open video file for writing`: this usually means no codec in the fallback list (`mp4v`, `XVID`, `MJPG`, `X264`) is available in your OpenCV build.
- Confirm the process has write permission to the `recordings/` directory (or the path set via `--recordings-dir`).
- Confirm at least one detection actually occurred; check the console for `Recording started; detected: [...]`.

### Video files exist but are 0 bytes or won't play

**Cause:** The process was killed (not stopped via `q`/`Esc`/Ctrl+C) while a recording was open, so `stop_recording()` never ran to finalize the file.

**Action:** Always stop with `q`/`Esc` in the window or Ctrl+C in the terminal so cleanup runs. In Docker, ensure `docker stop` is given enough time (default grace period is usually sufficient).

## Docker

### The container can't see the camera

**Cause:** `/dev/video0` (or the correct device path for your camera) was not passed into the container.

**Action:** Confirm `docker-compose.yml`'s `devices:` entry matches your camera's actual device path (`ls /dev/video*` on the host), and that your user has permission to access it.

### The preview window doesn't appear when running in Docker

**Cause:** This is expected. The default Docker command runs with `--no-window` since containers have no display. Recordings and logs are still produced normally.

## Quick Diagnostic Checklist

1. **Check the console/log output.** Every camera, detection, and recording event is logged with a timestamp.
2. **Check the log file** (see [Getting Started: Application Data](getting-started.md#application-data)) for a persistent record across runs.
3. **Verify the camera works outside ObjectTracker** (e.g. with your OS's default camera app) to rule out a hardware/driver issue.
4. **Run with `--log-level DEBUG`** for more detail.
5. **Test with `--objects all`** to rule out a class-name typo before suspecting the model or lighting.
