# Use the official Python 3.9 slim image as a base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install necessary dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port (if the script uses a web interface)
# EXPOSE 5000

# Default command to run the main script
CMD ["python", "src/main.py"]
