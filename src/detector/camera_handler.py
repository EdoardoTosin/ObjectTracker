import cv2
import logging

def initialize_camera(camera_index=0):
    """Initialize the camera and set maximum resolution dynamically."""
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logging.error("Error: Cannot open camera.")
            return None, None, None, None
        
        standard_resolutions = [
            (3840, 2160),  # 4K UHD
            (1920, 1080),  # Full HD
            (1280, 720),   # HD
            (640, 480)     # VGA
        ]

        selected_resolution = (640, 480)
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
    except Exception as e:
        logging.error(f"Failed to initialize camera: {e}")
        return None, None, None, None
