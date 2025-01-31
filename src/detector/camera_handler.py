from cv2 import CAP_PROP_FPS, CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, CAP_V4L2, VideoCapture
from platform import system
from logging import error, info

COMMON_RESOLUTIONS = [
    (3840, 2160),  # 4K UHD
    (1920, 1080),  # Full HD
    (1280, 720),   # HD
    (640, 480)     # VGA
]

FPS_VALUES = [120, 60, 30, 29.97, 24, 15, 10, 6, 5]

def initialize_camera(camera_index=0):
    """
    Initializes the camera and sets the highest supported resolution dynamically.
    Prints out compatible FPS values for each resolution.

    Args:
        camera_index (int, optional): The index of the camera (default is 0).

    Returns:
        tuple: (cap, frame_width, frame_height, fps)
    """
    try:
        system_os = system()
        
        if system_os in ["Linux"]:
            cap = VideoCapture(camera_index, CAP_V4L2)
        else:
            cap = VideoCapture(camera_index)
        
        if not cap.isOpened():
            error("Error: Cannot open camera.")
            return None, None, None, None
        
        selected_resolution = None
        selected_fps = None
        
        for width, height in COMMON_RESOLUTIONS:
            cap.set(CAP_PROP_FRAME_WIDTH, width)
            cap.set(CAP_PROP_FRAME_HEIGHT, height)
            actual_width = int(cap.get(CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(CAP_PROP_FRAME_HEIGHT))
            if (actual_width, actual_height) == (width, height):
                selected_resolution = (width, height)
                compatible_fps = set()
                for fps_value in FPS_VALUES:
                    cap.set(CAP_PROP_FPS, fps_value)
                    fps = cap.get(CAP_PROP_FPS)
                    if fps > 0:
                        compatible_fps.add(fps)
                
                sorted_fps = sorted(compatible_fps, reverse=True)
                info(f"Compatible FPS for resolution {width}x{height}: {sorted_fps}")
                selected_fps = sorted_fps[0] if sorted_fps else 30
                cap.set(CAP_PROP_FPS, selected_fps)
                break
        
        if not selected_resolution:
            selected_resolution = (320, 240)
            selected_fps = 10
        
        frame_width, frame_height = selected_resolution
        fps = selected_fps
        info(f"Camera configured: {frame_width}x{frame_height} @ {fps:.2f} FPS")
        return cap, frame_width, frame_height, fps
    except Exception as e:
        error(f"Failed to initialize camera: {e}")
        return None, None, None, None
