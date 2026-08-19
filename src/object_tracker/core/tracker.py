"""Main tracker loop: ties together the camera, detector, recorder, and HUD."""

from __future__ import annotations

import collections
import logging
import signal
import time
from datetime import datetime
from pathlib import Path
from types import FrameType

import cv2

from object_tracker.core.camera import CameraStream
from object_tracker.core.config import AppConfig, discover_model_paths
from object_tracker.core.constants import MAX_FAILED_CAPTURES, NORMAL_MODE_FPS
from object_tracker.core.detector import ObjectDetector, draw_detections
from object_tracker.core.fps_monitor import FrameRateMonitor
from object_tracker.core.overlay import draw_hud
from object_tracker.core.recorder import VideoRecorder
from object_tracker.core.timing import compute_buffer_frames, should_stop_recording

logger = logging.getLogger(__name__)

_WINDOW_NAME = "ObjectTracker (Live Feed)"
_QUIT_KEYS = {ord("q"), 27}  # 'q' or Esc
_REPORT_INTERVAL_SECONDS = 30.0


def _todays_recordings_dir(base: Path) -> Path:
    today = base / datetime.now().strftime("%Y-%m-%d")
    today.mkdir(parents=True, exist_ok=True)
    return today


def _reconnect(camera: CameraStream) -> bool:
    """Attempt to reconnect *camera*. Returns True on success."""
    logger.error("Too many failed captures; attempting reconnection...")
    try:
        camera.reconnect()
        logger.info("Camera reconnected.")
        return True
    except RuntimeError:
        logger.exception("Camera reconnection failed")
        return False


def run_tracker(config: AppConfig) -> int:
    """Run the object tracker until interrupted. Returns a process exit code."""
    model_paths = discover_model_paths(config.models_dir)

    if config.objects_to_detect is not None:
        from object_tracker.core.detector import load_class_names

        unknown = config.objects_to_detect - set(
            load_class_names(model_paths.class_file)
        )
        if unknown:
            logger.error("Unknown object class(es): %s", sorted(unknown))
            return 1

    detector = ObjectDetector(
        model_paths,
        objects_to_detect=config.objects_to_detect,
        confidence_threshold=config.confidence_threshold,
        nms_threshold=config.nms_threshold,
    )
    logger.info(
        "Detecting: %s",
        (
            "all classes"
            if config.objects_to_detect is None
            else sorted(config.objects_to_detect)
        ),
    )

    camera = CameraStream(config.camera_index)
    try:
        info = camera.open()
    except RuntimeError:
        logger.exception("Could not open camera")
        return 1
    logger.info("Camera ready: %dx%d @ %.2f FPS", info.width, info.height, info.fps)

    output_dir = _todays_recordings_dir(config.recordings_dir)
    base_fps = info.fps if config.dual_rate else max(info.fps, NORMAL_MODE_FPS)
    recorder = VideoRecorder(
        output_dir, info.width, info.height, base_fps, dual_rate=config.dual_rate
    )

    fps_monitor = FrameRateMonitor(initial_fps=info.fps) if config.dual_rate else None
    if config.dual_rate:
        logger.info("Dual-rate mode enabled (day/night adaptation).")

    state = {"stop": False}

    def _handle_signal(signum: int, _frame: FrameType | None) -> None:
        logger.info("Signal %s received; shutting down.", signum)
        state["stop"] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    buffer_frames = compute_buffer_frames(base_fps, config.buffer_seconds)
    frame_buffer: collections.deque = collections.deque(maxlen=buffer_frames)
    logger.info("Pre-detection buffer: %d frames", buffer_frames)

    last_detection_time = 0.0
    failed_captures = 0
    frame_count = 0
    last_report = time.time()

    try:
        while not state["stop"]:
            now = time.time()
            success, frame = camera.read()

            if not success:
                failed_captures += 1
                logger.warning(
                    "Frame capture failed (%d/%d)", failed_captures, MAX_FAILED_CAPTURES
                )
                if failed_captures >= MAX_FAILED_CAPTURES:
                    if not _reconnect(camera):
                        break
                    failed_captures = 0
                time.sleep(config.reconnect_interval)
                continue
            assert frame is not None  # guaranteed by success being True

            failed_captures = 0
            frame_count += 1

            current_fps = None
            if fps_monitor is not None:
                fps_monitor.update(now)
                current_fps = fps_monitor.current_fps
                if recorder.adapt_fps(fps_monitor.stable_fps) and recorder.is_recording:
                    logger.info("Restarting recording to apply new frame rate.")
                    recorder.stop_recording()

            detections = detector.detect(frame)
            detected_names = [d.class_name for d in detections]
            draw_detections(frame, detections)

            if detections:
                last_detection_time = now
                if not recorder.is_recording:
                    recorder.start_recording()
                    logger.info("Recording started; detected: %s", detected_names)
                    for buffered_frame, buffered_time in frame_buffer:
                        recorder.write_frame(buffered_frame, buffered_time)
            elif recorder.is_recording and should_stop_recording(
                last_detection_time, now, config.recording_duration
            ):
                recorder.stop_recording()
                logger.info(
                    "Recording stopped after %.0fs with no detections.",
                    config.recording_duration,
                )

            frame_buffer.append((frame.copy(), now))

            draw_hud(frame, detected_names, current_fps=current_fps, now=now)
            if recorder.is_recording:
                recorder.write_frame(frame, now)

            if config.show_window:
                cv2.imshow(_WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF in _QUIT_KEYS:
                    logger.info("Exit requested from the video window.")
                    break

            if now - last_report > _REPORT_INTERVAL_SECONDS:
                logger.info("Processing FPS: %.2f", frame_count / (now - last_report))
                if fps_monitor is not None:
                    logger.info(
                        "Camera FPS: %.2f (%s mode)",
                        fps_monitor.current_fps,
                        fps_monitor.mode.value,
                    )
                last_report = now
                frame_count = 0
    finally:
        recorder.release()
        camera.release()
        if config.show_window:
            cv2.destroyAllWindows()
        logger.info("Resources released. Exiting.")

    return 0
