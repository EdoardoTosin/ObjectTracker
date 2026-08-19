# Configuration

ObjectTracker is configured through [`config.yaml`](../config.yaml) and CLI flags. **CLI flags always take precedence** over the YAML file when explicitly passed; flags left at their default fall back to the YAML value, which in turn falls back to a built-in default.

## `config.yaml` Fields

| Key | Default | Description |
|---|---|---|
| `objects_to_detect` | `"all"` | `'all'`, or a comma-separated list of class names from `models/coco.names` (e.g. `"person, car, traffic light"`). |
| `recording_duration` | `30` | Seconds to keep recording after the last detection. |
| `buffer_seconds` | `10` | Seconds of pre-detection frames kept in a ring buffer, flushed to the file when a recording starts so the trigger moment isn't the first frame. |
| `reconnect_interval` | `5` | Seconds to wait between camera reconnection attempts after repeated read failures. |
| `confidence_threshold` | `0.45` | Minimum detection confidence (0-1) for a box to count as a match. |
| `nms_threshold` | `0.2` | Non-max suppression threshold (0-1); lower values remove more overlapping boxes. |
| `models_dir` | `models` | Directory containing the `.names` / `.pbtxt` / `.pb` model files. |
| `recordings_folder` | `recordings` | Directory recordings are written under. |

## CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--camera-index` | `0` | Index of the camera device to open. |
| `--objects` | *(from config.yaml)* | Overrides `objects_to_detect` for this run. |
| `--window` / `--no-window` | `--window` | Show or hide the live preview window. Use `--no-window` on headless systems. |
| `--dual-rate` / `--fixed-rate` | `--fixed-rate` | Enable frame-rate adaptation for day/night cameras. See [Getting Started](getting-started.md#dual-rate-daynight-cameras). |
| `--log-level` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `--config` | `config.yaml` (repo root) | Path to an alternate config file. |
| `--models-dir` | *(from config.yaml)* | Overrides `models_dir` for this run. |
| `--recordings-dir` | *(from config.yaml)* | Overrides `recordings_folder` for this run. |
| `--version`, `-V` | | Print the version number and exit. |

## Dual-Rate Thresholds

These are internal constants (`src/object_tracker/core/constants.py`), tuned for the common ~30 fps normal / ~4-5 fps night split and not currently exposed as config fields:

| Constant | Value | Purpose |
|---|---|---|
| `NIGHT_MODE_THRESHOLD_FPS` | `12.0` | Measured FPS below this is classified as night mode, above it, normal mode. Placed well clear of both the ~5 fps night ceiling and the ~30 fps normal floor so a few dropped or duplicated frames can't flip the classification. |
| `FPS_ADAPTATION_THRESHOLD` | `2.0` | Minimum FPS delta before the recorder adopts a new target rate. |
| `FPS_WINDOW_SIZE` | `30` | Number of frames averaged for the "stable" FPS estimate used to trigger a restart. |
| `MAX_FRAME_GAP_SECONDS` | `2.0` | Cap on how large a single frame-timing gap is treated as before duplicate-frame math applies. |
| `MAX_DUPLICATE_SECONDS` | `3.0` | Cap on how much duplicated playback time a single gap can insert. |

> [!TIP]
> If your camera's night mode runs outside the ~4-5 fps range, adjust `NIGHT_MODE_THRESHOLD_FPS` in `constants.py` accordingly. It only affects log labeling and internal classification, not the frame-duplication math, which always uses the actual measured rate.

## Detection Model

ObjectTracker ships with a pre-trained MobileNet SSD v3 model trained on COCO, stored in [`models/`](../models/):

| File | Purpose |
|---|---|
| `coco.names` | Ordered list of the 80 detectable class names. |
| `ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt` | Model graph configuration. |
| `frozen_inference_graph.pb` | Trained model weights. |

To use a different model, point `models_dir` (or `--models-dir`) at a directory containing your own `.names` / `.pbtxt` / `.pb` triplet with the same naming scheme.
