# ObjectTracker

This project performs real-time object detection using OpenCV's DNN module. It detects objects using a pre-trained MobileNet SSD model and records videos of detections.

## File Structure

- `models/`: Contains the pre-trained model files.
- `recordings/`: Stores the recorded video files.
- `src/`: Contains the main Python code for object detection and configuration.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/EdoardoTosin/ObjectTracker
   cd ObjectTracker
   ```

2. Install required Python dependencies:
   ```bash
   pip install -r requirements.txt --user
   ```

## Usage

Run the object detection script:

```bash
python src/object_detector.py
```

This will begin detecting objects from the camera and start recording when an object is detected.

## Configuration

- The `config.py` file contains paths to the models and settings for object detection.
- You can modify the objects to detect by changing the `objects_to_detect` list in the `config.py`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
