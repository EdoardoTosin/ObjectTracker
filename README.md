# ObjectTracker

ObjectTracker is a lightweight, real-time object detection and video recording tool built for Raspberry Pi, Linux, and Windows. It uses OpenCV's DNN module with a pre-trained MobileNet SSD model to detect specified objects and automatically start recording when detections occur.

## Features

- **Real-time Object Detection**: Detect specified objects in real-time using OpenCV's DNN module and MobileNet SSD.
 
- **Event-based Video Recording**: Automatically starts recording when objects are detected, with a configurable duration to continue recording after the last detection.

- **Customizable Detection**: Supports detection of specific objects or all detectable classes via CLI arguments or configuration files.

- **Automatic Camera Reconnection**: Automatically attempts to reconnect in case of camera disconnection during runtime.

- **Organized Video Storage**: Videos are saved in a structured format under the `recordings/` folder, organized by date.

- **Docker Support**: Deploy effortlessly using Docker with an optional `docker-compose.yml` setup.

## Installation

### Method 1: Using Python Directly

1. **Clone the repository**
   
   First, clone the repository to your local machine by running:
   
   ```bash
   git clone https://github.com/EdoardoTosin/ObjectTracker
   cd ObjectTracker
   ```

2. **Install dependencies**
   
   Ensure you have Python 3.9+ installed. If not, you can download it from the official Python website. Once you have the correct version, install the necessary Python dependencies:
   
   ```bash
   pip install --user -r requirements.txt
   ```
   
   This command installs the required packages, including those needed for object detection.

### Method 2: Using Docker (for containerized setup)

1. **Install Docker**
   
   If you don’t have Docker installed, you can download and install it from [Docker's website](https://www.docker.com/get-started).

2. **Clone the repository**
   
   As with the Python method, first clone the repository to your local machine:
   
   ```bash
   git clone https://github.com/EdoardoTosin/ObjectTracker
   cd ObjectTracker
   ```

3. **Build the Docker image**
   
   Build the Docker image for the project using the following command:
   
   ```bash
   docker build -t object-tracker .
   ```

4. **Run the Docker container**
   
   Run the container, mapping the `recordings` folder to your local machine’s folder for easy access:
   
   ```bash
   docker run --rm -v $(pwd)/recordings:/app/recordings object-tracker
   ```
   
   This will start the application within the Docker container. You can modify the path to the `recordings` folder if needed.

5. **Alternatively: Use Docker Compose**
   
   If you'd like an even easier setup with pre-configured environment settings, you can use Docker Compose. Run the following command:
   
   ```bash
   docker-compose up --build
   ```
   
   Docker Compose will handle the image build and container execution automatically.

## Usage

### 1. Running the object detection system

- **Using Python directly**:
   
   To run the object detection system, execute the following command:
   
   ```bash
   python src/main.py
   ```

- **Using Docker**:

   After building and running the Docker container, it will automatically start the object detection system.

### 2. Detect specific objects

To detect specific objects like a "person" or "car," use the `--objects` flag followed by a comma-separated list of object names. Whitespace around names is automatically trimmed:

```bash
python src/main.py --objects person, car, traffic light
```

- **Note**: Both `person, car, traffic light` and `person , car , traffic light` are handled correctly.

- **Using Docker**:
   
   If running via Docker, this step should be handled by passing the same arguments during container execution.

### 3. Detect all objects

To detect all objects, use the `--objects` flag with the value `all`:

```bash
python src/main.py --objects all
```

- **Using Docker**:
   
   You can modify the Docker command to pass the desired arguments in the same way.

### 4. View Available Command-Line Options

To get a full list of available options, run:

```bash
python src/main.py --help
```

This will show you all available parameters, including those for specifying which objects to detect, input files, output formats, etc.

- **Using Docker**:
   
   The same command applies in the Docker container as well for accessing available help options.

## Configuration

The main configuration file is `config/config.yaml`. You can customize parameters like objects to detect, recording duration, and buffer size.

### Key Configuration Parameters

- **Objects to Detect**
  Specify a comma-separated list of object names (whitespace is automatically trimmed) or use `"all"` to detect everything:
  ```yaml
  objects_to_detect: "person, car, traffic light"
  ```

  To detect all objects:
  ```yaml
  objects_to_detect: all
  ```

- **Recording Settings**
  Control the recording behavior:
  ```yaml
  recording_duration: 30        # Duration in seconds to keep recording after the last detection
  buffer_size: 50               # Number of frames to buffer before starting recording
  reconnect_interval: 5         # Time in seconds to wait before attempting camera reconnection
  ```

- **Output Folder**
  Specify a custom folder for recordings:
  ```yaml
  recordings_folder: "path/to/custom/folder"
  ```

## File Descriptions

### `src/main.py`

The main script that initializes the detection system, manages camera input, and handles video recording.

### `config/config.yaml`

Contains user-defined parameters like object detection list, recording duration, and buffer settings.

### `detector/object_detector.py`

Implements object detection logic using OpenCV's DNN module, processing frames and identifying specified objects.

### `detector/recorder.py`

Handles video recording, buffering frames, and saving videos to the `recordings/` folder.

### `docker-compose.yml`

Simplifies deployment in a Docker environment, managing volume mounting and build steps.

## Customization

### Changing Camera Index

If multiple cameras are available, use the `--camera-index` argument to specify which one to use:

```bash
python src/main.py --camera-index 1
```

### Specifying Objects to Detect

You can define the objects to detect either in `config.yaml` or directly via CLI arguments:

```bash
python src/main.py --objects "person, car, traffic light"
```

## Contributing

Contributions are welcome! Follow these steps to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -am 'Add a new feature'`).
4. Push the branch (`git push origin feature/your-feature`).
5. Create a pull request.

Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Acknowledgments

This project was built using:

- [OpenCV](https://opencv.org/)
- Pre-trained MobileNet SSD model
- Python 3.9+
- Docker
