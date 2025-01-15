import os
from datetime import datetime

# Get the directory of the current script
base_path = os.path.dirname(os.path.abspath(__file__))  

# Get the root directory of the project (one level up from the current script)
project_root = os.path.dirname(base_path)

# Define the path to the models directory, which is located in the root of the project
model_path = os.path.join(project_root, "models")

# Automatically find the files in the models folder based on extension
classFile = None
configPath = None
weightsPath = None

# Loop through the files in the models directory and assign the paths based on extensions
for filename in os.listdir(model_path):
    file_path = os.path.join(model_path, filename)
    if filename.endswith(".names"):
        classFile = file_path  # Assign the path to the coco.names file
    elif filename.endswith(".pbtxt"):
        configPath = file_path  # Assign the path to the model configuration file
    elif filename.endswith(".pb"):
        weightsPath = file_path  # Assign the path to the model weights file

# Check if all required files are found
if classFile is None or configPath is None or weightsPath is None:
    raise FileNotFoundError("One or more required model files are missing in the 'models' folder.")

# Objects to detect (can be a single object or a list)
objects_to_detect = ['cat']  # Change this list as needed

# Recording settings
recordings_folder = os.path.join(project_root, "recordings")  # Folder for storing recordings
recording_duration = 30  # Seconds to keep recording after last detection
buffer_size = 50  # Number of frames to buffer before starting recording
reconnect_interval = 5  # Seconds to wait before trying to reconnect the camera

# Function to ensure a dedicated folder structure for recordings
def ensure_recordings_folder():
    if not os.path.exists(recordings_folder):
        os.makedirs(recordings_folder)

# Get today's subfolder for recordings
def get_today_folder():
    today_folder = os.path.join(recordings_folder, datetime.now().strftime('%Y-%m-%d'))
    if not os.path.exists(today_folder):
        os.makedirs(today_folder)
    return today_folder
