from os import makedirs, path
from datetime import datetime
from logging import error, info

def ensure_folder_exists(folder_path):
    """
    Ensures that a specified folder exists. If it doesn't, creates it.
    
    Args:
        folder_path (str): Path to the folder to be checked/created.
    """
    try:
        if not path.exists(folder_path):
            makedirs(folder_path)
            info(f"Folder created: {folder_path}")
    except Exception as e:
        error(f"Failed to create folder {folder_path}: {e}")
        raise

def get_today_folder(base_folder):
    """
    Creates and returns the path to today's subfolder inside a given base folder.
    
    Args:
        base_folder (str): Path to the base folder where today's folder will be created.
    
    Returns:
        str: Full path to today's folder.
    """
    today_folder = path.join(base_folder, datetime.now().strftime('%Y-%m-%d'))
    ensure_folder_exists(today_folder)
    return today_folder

def get_timestamped_filename(extension="mp4"):
    """
    Generates a filename with a timestamp, suitable for recorded video files.
    
    Args:
        extension (str): File extension for the generated filename.
    
    Returns:
        str: A timestamped filename with the specified extension.
    """
    return f"detection_{datetime.now().strftime('%H-%M-%S')}.{extension}"
