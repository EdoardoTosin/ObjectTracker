import os
import cv2
from datetime import datetime
import logging

class VideoRecorder:
    """
    A utility class for handling video recording operations.
    """
    
    def __init__(self, output_folder, frame_width, frame_height, fps, codec='mp4v'):
        """
        Initializes the VideoRecorder instance.
        
        Args:
            output_folder (str): Path to the folder where recordings will be saved.
            frame_width (int): Width of the video frames.
            frame_height (int): Height of the video frames.
            fps (float): Frames per second for the video.
            codec (str): FourCC codec for video encoding (default: 'mp4v').
        """
        self.output_folder = output_folder
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.codec = codec if isinstance(codec, str) and len(codec) == 4 else 'mp4v'
        self.output = None
        self.recording = False
    
    def start_recording(self, frame):
        """
        Starts a new video recording with the given frame.
        
        Args:
            frame (numpy.ndarray): The first frame to include in the recording.
        """
        try:
            filename = f"detection_{datetime.now().strftime('%H-%M-%S')}_{self.frame_width}x{self.frame_height}_{int(self.fps)}fps.mp4"
            file_path = os.path.join(self.output_folder, filename)
            
            ensure_folder_exists(self.output_folder)
            
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            self.output = cv2.VideoWriter(file_path, fourcc, self.fps, (self.frame_width, self.frame_height))
            if not self.output.isOpened():
                raise IOError(f"Failed to open video file for writing: {file_path}")
            
            self.recording = True
            self.output.write(frame)  # Write the first frame immediately
            logging.info(f"Recording started: {file_path}")
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.output = None
            self.recording = False
    
    def write_frame(self, frame):
        """
        Writes a frame to the recording.
        
        Args:
            frame (numpy.ndarray): The frame to be written.
        """
        if self.recording and self.output:
            self.output.write(frame)
    
    def stop_recording(self):
        """
        Stops the recording and releases the output file.
        """
        if self.recording and self.output:
            self.output.release()
            self.output = None
            self.recording = False
            logging.info("Recording stopped.")