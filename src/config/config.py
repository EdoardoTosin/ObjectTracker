from os import listdir, makedirs, path
from yaml import safe_load
from datetime import datetime

# Default configuration values
DEFAULT_RECORDING_DURATION = (
    30  # Duration (in seconds) to continue recording after the last detection
)
DEFAULT_BUFFER_SIZE = 50  # Number of frames to buffer before initiating recording
DEFAULT_RECONNECT_INTERVAL = (
    5  # Interval (in seconds) to wait before attempting to reconnect the camera
)
DEFAULT_OBJECTS_TO_DETECT = "all"  # Default setting to detect all objects

# Define key paths for models and recordings
base_path = path.dirname(path.abspath(__file__))  # Path of the current config script
project_root = path.dirname(path.dirname(base_path))  # Root path of the project
model_path = path.join(
    project_root, "models"
)  # Path to the folder containing model files
recordings_folder = path.join(
    project_root, "recordings"
)  # Path for storing video recordings

# Initialize variables for required model files
classFile, configPath, weightsPath = None, None, None

# Automatically detect and assign paths for required model files based on their extensions
for filename in listdir(model_path):
    file_path = path.join(model_path, filename)
    if filename.endswith(".names"):
        classFile = file_path  # Class names file (list of object classes)
    elif filename.endswith(".pbtxt"):
        configPath = file_path  # Configuration file for the object detection model
    elif filename.endswith(".pb"):
        weightsPath = file_path  # Pre-trained model weights

# Raise an error if any required model file is missing
if None in (classFile, configPath, weightsPath):
    raise FileNotFoundError("One or more required model files are missing in 'models'.")


def parse_objects_string(objects_string):
    """
    Parse a comma-separated string of objects, trimming spaces around each object.

    Args:
        objects_string (str): Comma-separated string of objects (e.g., 'person, car, traffic light').

    Returns:
        list: List of trimmed object names (e.g., ['person', 'car', 'traffic light']).
    """
    return (
        ["all"]
        if objects_string.lower() == "all"
        else [obj.strip() for obj in objects_string.split(",")]
    )


# Load user-specific configuration from the 'config.yaml' file, if available
config_file_path = path.join(base_path, "config.yaml")
if path.exists(config_file_path):
    with open(config_file_path, "r") as file:
        user_config = safe_load(file)  # Load YAML configuration as a dictionary
else:
    user_config = {}

# Apply user-specific configurations, falling back to defaults if not specified
objects_to_detect = parse_objects_string(
    user_config.get("objects_to_detect", DEFAULT_OBJECTS_TO_DETECT)
)
recording_duration = user_config.get("recording_duration", DEFAULT_RECORDING_DURATION)
buffer_size = user_config.get("buffer_size", DEFAULT_BUFFER_SIZE)
reconnect_interval = user_config.get("reconnect_interval", DEFAULT_RECONNECT_INTERVAL)
recordings_folder = user_config.get("recordings_folder", recordings_folder)


def ensure_recordings_folder():
    """
    Ensure that the recordings folder exists by creating it if necessary.
    """
    if not path.exists(recordings_folder):
        makedirs(recordings_folder)


def get_today_folder():
    """
    Create and return a subfolder named with the current date inside the recordings folder.

    The folder name is based on the format 'YYYY-MM-DD'.

    Returns:
        str: Path to today's recordings folder.
    """
    today_folder = path.join(recordings_folder, datetime.now().strftime("%Y-%m-%d"))
    if not path.exists(today_folder):
        makedirs(today_folder)
    return today_folder
