#!/bin/bash

# Build the Docker image for bash_exec environment
# Usage: ./build_docker_image.sh

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Building Docker image for bash_exec environment..."

# Build the Docker image
docker build \
    -t bash_exec_environment:latest \
    -f "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR"

echo "Docker image built successfully!"
echo "Image name: bash_exec_environment:latest"

