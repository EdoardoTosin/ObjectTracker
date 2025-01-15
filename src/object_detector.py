import cv2
import time
import logging
import argparse
from datetime import datetime
from collections import deque
from config import (
    classFile, configPath, weightsPath,
    objects_to_detect, recording_duration, buffer_size, reconnect_interval, 
    ensure_recordings_folder, get_today_folder
)
import os
import signal
import sys

# Constants
CONFIDENCE_THRESHOLD = 0.45  # Minimum confidence for detecting an object
NMS_THRESHOLD = 0.2          # Non-max suppression threshold for overlapping boxes

# Set up logging with reduced verbosity
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

# Load class labels from the .names file
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Initialize the pre-trained object detection model
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)              # Smaller input size for faster processing
net.setInputScale(1.0 / 127.5)          # Normalize input scale
net.setInputMean((127.5, 127.5, 127.5)) # Mean subtraction for RGB normalization
net.setInputSwapRB(True)                # Swap Red and Blue channels for OpenCV compatibility

# Graceful shutdown handling
def cleanup(cap, output):
    """Release resources and close OpenCV windows."""
    if cap is not None:
        cap.release()
    if output is not None:
        output.release()
    cv2.destroyAllWindows()
    logging.info("Resources released. Exiting program.")

def signal_handler(sig, frame):
    """Handle system signals for graceful shutdown."""
    logging.info("Interrupt received. Cleaning up...")
    cleanup(cap, output)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Handle termination signals

def initialize_camera(camera_index=0):
    """
    Initialize the camera and select the highest supported resolution.
    
    Args:
        camera_index (int): Index of the camera to use.
    
    Returns:
        cap (cv2.VideoCapture): Camera capture object.
        frame_width (int): Selected frame width.
        frame_height (int): Selected frame height.
        fps (float): Frames per second.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logging.error("Error: Cannot open camera.")
        return None, None, None, None

    # Try common resolutions and pick the highest supported
    standard_resolutions = [
        (3840, 2160),  # 4K UHD
        (1920, 1080),  # Full HD
        (1280, 720),   # HD
        (640, 480)     # VGA
    ]
    
    selected_resolution = (640, 480)  # Default resolution
    for width, height in standard_resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if (actual_width, actual_height) == (width, height):
            selected_resolution = (width, height)
            break
    
    frame_width, frame_height = selected_resolution
    fps = cap.get(cv2.CAP_PROP_FPS)
    logging.info(f"Camera configured: {frame_width}x{frame_height} @ {fps:.2f} FPS")
    return cap, frame_width, frame_height, fps

def getObjects(img, thres=CONFIDENCE_THRESHOLD, nms=NMS_THRESHOLD, objects=[]):
    """
    Detect objects in a frame using the pre-trained model.
    
    Args:
        img (numpy.ndarray): Input image frame.
        thres (float): Confidence threshold.
        nms (float): Non-max suppression threshold.
        objects (list): List of objects to detect.
    
    Returns:
        img (numpy.ndarray): Annotated image.
        objectInfo (list): List of detected objects with bounding boxes and confidence scores.
    """
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className, confidence])
                cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                cv2.putText(img, f"{className.upper()} {round(confidence * 100, 2)}%", 
                            (box[0] + 10, box[1] + 30), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 255, 0), 2)
    return img, objectInfo

if __name__ == "__main__":
    ensure_recordings_folder()
    parser = argparse.ArgumentParser(description="Object detection with camera.")
    parser.add_argument("--camera_index", type=int, default=0, help="Index of the camera to use.")
    args = parser.parse_args()
    
    cap, frame_width, frame_height, fps = initialize_camera(args.camera_index)
    if cap is None:
        sys.exit("Error: Unable to initialize the camera.")
    
    recording = False
    last_detection_time = 0
    buffer_frames = deque(maxlen=buffer_size)
    output = None
    
    while True:
        success, img = cap.read()
        if not success:
            logging.warning("Frame capture failed. Retrying...")
            time.sleep(reconnect_interval)
            continue
        
        buffer_frames.append(img.copy())
        result, objectInfo = getObjects(img, objects=objects_to_detect)
        
        detected = len(objectInfo) > 0
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(img, f"Time: {timestamp}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(img, f"Objects Detected: {len(objectInfo)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        if detected:
            if not recording:
                today_folder = get_today_folder()
                filename = f"detection_{datetime.now().strftime('%H-%M-%S')}_{frame_width}x{frame_height}_{int(fps)}fps.mp4"
                file_path = os.path.join(today_folder, filename)
                output = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
                recording = True
                logging.info(f"Recording started: {file_path}")

                while buffer_frames:
                    output.write(buffer_frames.popleft())

            last_detection_time = time.time()
        
        if recording:
            output.write(img)
            if time.time() - last_detection_time > recording_duration:
                recording = False
                output.release()
                output = None
                logging.info("Recording stopped.")

        cv2.imshow("Object Detector", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cleanup(cap, output)
