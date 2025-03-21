import logging
import signal
from functools import partial
import sys
import cv2
import argparse
import time
import collections
from detector.camera_handler import initialize_camera
from detector.object_detector import ObjectDetector
from detector.recorder import VideoRecorder
from config.config import (
    recording_duration,
    buffer_size,
    reconnect_interval,
    ensure_recordings_folder,
    get_today_folder,
    objects_to_detect as default_objects,
)

# Configure logging to display timestamp, log level, and message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)


def cleanup(camera, recorder):
    """
    Release resources and clean up before exiting.

    Args:
        camera (cv2.VideoCapture): OpenCV camera object.
        recorder (VideoRecorder): Video recorder instance managing video output.
    """
    if camera:
        camera.release()
    if recorder and recorder.recording:
        recorder.stop_recording()
    logging.info("Resources released. Exiting program.")


def signal_handler(sig, frame, camera, recorder):
    """
    Handle system signals (SIGINT, SIGTERM) for graceful shutdown.
    Calls the cleanup function to release resources and close the program.

    Args:
        sig (int): Signal number.
        frame (FrameType): Current stack frame (unused in this context).
        camera (cv2.VideoCapture): OpenCV camera object.
        recorder (VideoRecorder): Video recorder instance managing video output.
    """
    logging.info("Interrupt received. Cleaning up...")
    cleanup(camera, recorder)
    cv2.destroyAllWindows()
    sys.exit(0)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments to configure script behavior.

    Returns:
        argparse.Namespace: Parsed arguments including options for camera, objects, and logging level.
    """
    parser = argparse.ArgumentParser(description="Object Tracker with Video Recording")

    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Disable live video feed window (default: enabled)",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Index of the camera to use (default: 0)",
    )
    parser.add_argument(
        "--objects",
        type=str,
        default=None,
        help=(
            "Comma-separated list of objects to detect (e.g., 'person,car,traffic light'). "
            "Use 'all' to detect all objects or leave empty to use the default from config."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    return parser.parse_args()


def validate_objects_to_detect(objects, class_file_path):
    """
    Validate that all specified objects are present in the .names file.

    Args:
        objects (list): List of object names to detect.
        class_file_path (str): Path to the .names file containing valid object classes.

    Raises:
        ValueError: If any object is not found in the .names file.
    """
    if objects == ["all"]:
        return  # Skip validation if 'all' is specified

    with open(class_file_path, "r") as f:
        valid_classes = set(f.read().strip().split("\n"))

    missing_objects = [obj for obj in objects if obj not in valid_classes]

    if missing_objects:
        logging.error(f"Invalid objects specified: {missing_objects}")
        raise ValueError(f"Objects not found in .names file: {missing_objects}")

    logging.info(f"All specified objects are valid: {objects}")


def main():
    # Parse and handle command-line arguments
    args = parse_arguments()

    # Set the global logging level based on user input
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Ensure that the recordings folder structure exists
    try:
        ensure_recordings_folder()
    except Exception as e:
        logging.error(f"Error while ensuring recordings folder: {e}")
        sys.exit(1)  # Exit if folder creation fails

    # Initialize camera and retrieve its properties
    camera, frame_width, frame_height, fps = None, 0, 0, 0
    try:
        camera, frame_width, frame_height, fps = initialize_camera(args.camera_index)
        logging.info(
            f"Initialized camera with {frame_width}x{frame_height} at {fps:.2f} FPS."
        )
        if not camera:
            raise RuntimeError("Unable to initialize the camera.")
    except Exception as e:
        logging.error(f"Error initializing camera: {e}")
        sys.exit(1)

    # Set up signal handling for SIGINT and SIGTERM to allow graceful shutdown
    recorder = None
    signal.signal(
        signal.SIGINT, partial(signal_handler, camera=camera, recorder=recorder)
    )
    signal.signal(
        signal.SIGTERM, partial(signal_handler, camera=camera, recorder=recorder)
    )

    # Configure object detection based on user arguments or default settings
    object_list = None
    try:
        if args.objects:
            object_list = [
                obj.strip() for obj in args.objects.split(",")
            ]  # Trim spaces around separators
            if "all" in object_list:
                detector = ObjectDetector(None)  # Detect all possible objects
                logging.info("Detecting all possible objects.")
            else:
                from config.config import classFile  # Import path to .names file

                validate_objects_to_detect(
                    object_list, classFile
                )  # Validate specified objects
                detector = ObjectDetector(object_list)
                logging.info(f"Detecting specified objects: {object_list}")
        elif default_objects == "all":
            detector = ObjectDetector(None)  # Detect all possible objects (from config)
            logging.info("Detecting all possible objects (default config).")
        else:
            from config.config import classFile  # Import path to .names file

            validate_objects_to_detect(
                default_objects, classFile
            )  # Validate default objects
            detector = ObjectDetector(default_objects)
            logging.info(f"Detecting specified objects from config: {default_objects}")
    except Exception as e:
        logging.error(f"Error setting up object detection: {e}")
        cleanup(camera, recorder)
        sys.exit(1)

    # Prepare the video recorder and set output folder
    try:
        output_folder = get_today_folder()
    except Exception as e:
        logging.error(f"Error while creating today's folder: {e}")
        cleanup(camera, recorder)  # Ensure resources are released before exiting
        sys.exit(1)  # Exit if folder creation fails

    recorder = VideoRecorder(
        output_folder, frame_width, frame_height, fps, codec="mp4v"
    )

    last_detection_time = 0  # Track the time of the last detection
    frame_interval = 1.0 / fps  # Time interval between frames based on FPS
    frame_buffer = collections.deque(maxlen=int(fps * 5))  # Buffer frames

    logging.info("Press 'q' or 'Esc' to exit the program.")

    try:
        while True:
            start_time = time.time()
            success, frame = camera.read()
            if not success:
                logging.warning("Frame capture failed. Retrying...")
                time.sleep(
                    reconnect_interval
                )  # Pause briefly before retrying to reduce CPU usage
                continue

            # Store frames in buffer for pre-recording effect
            frame_buffer.append(frame.copy())

            # Detect objects in the current frame
            detected_objects = detector.detect(frame)
            current_time = time.time()
            detected_names = []

            if detected_objects:
                last_detection_time = current_time
                detected_names = [obj[1] for obj in detected_objects]
                if not recorder.recording:
                    recorder.start_recording()
                    logging.info(f"Started recording. Detected: {detected_names}")
                    for buffered_frame in frame_buffer:  # Write buffered frames
                        recorder.write_frame(buffered_frame)
            elif recorder.recording and (
                current_time - last_detection_time > recording_duration
            ):
                recorder.stop_recording()
                logging.info("Stopped recording after timeout (no detections).")

            # Overlay timestamp and detected object information on the frame
            timestamp = time.strftime("%Y-%m-%d %a %H:%M:%S")
            detected_info = (
                "Detected: " + ", ".join(detected_names)
                if detected_objects
                else "No objects detected"
            )

            cv2.putText(
                frame,
                timestamp,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                detected_info,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            # Write the frame to the video file if recording
            recorder.write_frame(frame)

            elapsed_time = time.time() - start_time
            delay = max(0, frame_interval - elapsed_time)
            time.sleep(delay)

            # Display the live video feed if the window option is enabled
            if not args.no_window:
                cv2.imshow("Live Feed", frame)
                if cv2.waitKey(1) & 0xFF in [
                    ord("q"),
                    27,
                ]:  # Exit on 'q' or 'Esc' key press
                    logging.info("User requested exit. Cleaning up...")
                    break
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Ensure cleanup occurs no matter what
        cleanup(camera, recorder)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
