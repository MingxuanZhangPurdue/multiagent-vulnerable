#!/bin/bash

# Start Flask server for index1
python3 /app/index1-server.py &

# Start socket server for index10
python3 /app/index10-server.py &

# Wait for all background processes
wait

