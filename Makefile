# Project-specific variables
PYTHON := python3
PIP := pip3
MAIN_SCRIPT := src/main.py
CONFIG_DIR := config
DETECTOR_DIR := detector
VENV_DIR := venv

# Virtual environment setup
VENV_BIN := $(VENV_DIR)/bin
ACTIVATE := . $(VENV_BIN)/activate

# Define Python commands within the virtual environment
PYTHON_VENV := $(VENV_BIN)/$(PYTHON)
PIP_VENV := $(VENV_BIN)/$(PIP)

# Docker variables
IMAGE_NAME := object-tracker
CONTAINER_NAME := object-tracker-container

# Default target: show help
.DEFAULT_GOAL := help

# Install dependencies
install: $(VENV_DIR)
	@echo "Installing dependencies..."
	$(PIP_VENV) install -r requirements.txt
	@echo "Dependencies installed."

$(VENV_DIR):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)

# Run the main script
run: install
	@echo "Running the main script..."
	$(PYTHON_VENV) $(MAIN_SCRIPT)

# Lint the code using flake8 for style and PEP8 compliance
lint:
	@echo "Running linter..."
	$(PYTHON_VENV) -m flake8 $(MAIN_SCRIPT) $(DETECTOR_DIR) $(CONFIG_DIR)

# Clean temporary files and logs
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	@echo "Temporary files cleaned."

# Clean and remove the virtual environment
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "All cleaned."

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .
	@echo "Docker image built: $(IMAGE_NAME)"

# Run the container
docker-run: docker-build
	@echo "Running Docker container..."
	docker run --rm -v $(PWD)/recordings:/app/recordings $(IMAGE_NAME)
	@echo "Docker container stopped."

# Clean Docker images (optional)
docker-clean:
	@echo "Removing Docker image..."
	docker rmi $(IMAGE_NAME)
	@echo "Docker image removed."

# Display help information
help:
	@echo "Available commands:"
	@echo "  make install      - Create a virtual environment and install dependencies"
	@echo "  make run          - Run the main script"
	@echo "  make lint         - Run the linter on the codebase"
	@echo "  make clean        - Remove temporary files and logs"
	@echo "  make clean-all    - Remove virtual environment and temporary files"
	@echo "  make docker-build - Build the Docker image"
	@echo "  make docker-run   - Run the Docker container"
	@echo "  make docker-clean - Remove the Docker image"
