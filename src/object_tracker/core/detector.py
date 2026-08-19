"""Object detection using OpenCV's DNN module with an SSD MobileNet model.

Detection and rendering are kept separate: :meth:`ObjectDetector.detect`
returns plain data and never mutates the frame, so it can be tested and
reasoned about independently of :func:`draw_detections`.
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

import cv2
import numpy as np

from object_tracker.core.config import ModelPaths
from object_tracker.core.constants import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_NMS_THRESHOLD,
    DETECTOR_INPUT_MEAN,
    DETECTOR_INPUT_SCALE,
    DETECTOR_INPUT_SIZE,
)

logger = logging.getLogger(__name__)

_BOX_COLOR = (0, 255, 0)


@dataclasses.dataclass(frozen=True)
class Detection:
    """A single detected object."""

    box: tuple[int, int, int, int]  # x, y, width, height
    class_name: str
    confidence: float


def load_class_names(class_file: Path) -> list[str]:
    """Read a newline-separated ``.names`` file into an ordered class list."""
    return Path(class_file).read_text(encoding="utf-8").strip().split("\n")


class ObjectDetector:
    """Wraps an OpenCV DNN SSD model and filters detections by class name."""

    def __init__(
        self,
        model_paths: ModelPaths,
        objects_to_detect: frozenset[str] | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
    ) -> None:
        self.class_names = load_class_names(model_paths.class_file)
        self.objects_to_detect = (
            frozenset(self.class_names)
            if objects_to_detect is None
            else objects_to_detect
        )
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        net = cv2.dnn.readNetFromTensorflow(
            str(model_paths.weights_file), str(model_paths.config_file)
        )
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        self._model = cv2.dnn_DetectionModel(net)  # type: ignore[attr-defined]
        self._model.setInputSize(*DETECTOR_INPUT_SIZE)
        self._model.setInputScale(DETECTOR_INPUT_SCALE)
        self._model.setInputMean(DETECTOR_INPUT_MEAN)
        self._model.setInputSwapRB(True)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run inference on *frame* and return detections matching the configured classes."""
        try:
            class_ids, confidences, boxes = self._model.detect(
                frame,
                confThreshold=self.confidence_threshold,
                nmsThreshold=self.nms_threshold,
            )
        except cv2.error:
            logger.exception("Object detection failed")
            return []

        if class_ids is None or len(class_ids) == 0:
            return []

        detections = []
        for class_id, confidence, box in zip(
            class_ids.flatten(), confidences.flatten(), boxes
        ):
            class_name = self.class_names[class_id - 1]
            if class_name in self.objects_to_detect:
                x, y, w, h = (int(v) for v in box)
                detections.append(
                    Detection(
                        box=(x, y, w, h),
                        class_name=class_name,
                        confidence=float(confidence),
                    )
                )
        return detections


def draw_detections(frame: np.ndarray, detections: list[Detection]) -> None:
    """Draw bounding boxes and labels for *detections* directly onto *frame*."""
    for detection in detections:
        x, y, w, h = detection.box
        cv2.rectangle(frame, (x, y, w, h), color=_BOX_COLOR, thickness=2)
        cv2.putText(
            frame,
            f"{detection.class_name.upper()} {detection.confidence * 100:.1f}%",
            (x + 10, y + 30),
            cv2.FONT_HERSHEY_COMPLEX,
            0.6,
            _BOX_COLOR,
            2,
        )
