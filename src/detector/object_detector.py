from cv2 import dnn, dnn_DetectionModel, FONT_HERSHEY_COMPLEX, putText, rectangle
from config.config import classFile, configPath, weightsPath
from logging import error


class ObjectDetector:
    def __init__(self, objects_to_detect=None):
        """
        Initialize the object detector.
        If objects_to_detect is None, detect all available classes.
        """
        with open(classFile, "r") as f:
            self.classNames = f.read().strip().split("\n")

        net = dnn.readNetFromTensorflow(weightsPath, configPath)
        net.setPreferableBackend(dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(dnn.DNN_TARGET_CPU)
        self.net = dnn_DetectionModel(net)
        self.net.setInputSize(320, 320)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)

        if objects_to_detect is None:  # Detect all objects if None
            self.objects_to_detect = set(self.classNames)
        else:
            self.objects_to_detect = set(objects_to_detect)

    def detect(self, frame, confidence_threshold=0.45, nms_threshold=0.2):
        """
        Detect objects in a frame.

        Args:
            frame (ndarray): Input frame from the video feed.
            confidence_threshold (float): Minimum confidence for detections.
            nms_threshold (float): Non-max suppression threshold.

        Returns:
            detected_objects (list): List of detected objects, each represented as a tuple
                                     (bounding box, class name, confidence).
        """
        detected_objects = []
        try:
            classIds, confs, bbox = self.net.detect(
                frame, confThreshold=confidence_threshold, nmsThreshold=nms_threshold
            )

            if classIds is not None and len(classIds) != 0:
                for classId, confidence, box in zip(
                    classIds.flatten(), confs.flatten(), bbox
                ):
                    className = self.classNames[classId - 1]
                    if className in self.objects_to_detect:
                        detected_objects.append((box, className, confidence))
                        rectangle(frame, box, color=(0, 255, 0), thickness=2)
                        putText(
                            frame,
                            f"{className.upper()} {round(confidence * 100, 2)}%",
                            (box[0] + 10, box[1] + 30),
                            FONT_HERSHEY_COMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
        except Exception as e:
            error(f"Object detection failed: {e}")

        return detected_objects
