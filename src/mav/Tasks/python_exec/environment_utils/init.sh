#!/bin/bash

# Initialize the container environment
echo "Initializing container..."

# Start background processes
/app/start_processes.sh &

# Keep container running
tail -f /dev/null

