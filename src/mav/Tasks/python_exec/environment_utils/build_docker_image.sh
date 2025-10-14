#!/bin/bash

# Build the Docker image for python_exec environment
# Usage: ./build_docker_image.sh [is_OCI]

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default is_OCI value
is_OCI=${1:-false}

echo "Building Docker image for python_exec environment..."
echo "is_OCI: $is_OCI"

# Build the Docker image
docker build \
    -t python_exec_environment:latest \
    --build-arg is_OCI=$is_OCI \
    -f "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR"

echo "Docker image built successfully!"
echo "Image name: python_exec_environment:latest"

