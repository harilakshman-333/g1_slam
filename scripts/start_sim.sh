#!/bin/bash
# Start Stage A — Simulation
# Launches Gazebo + SLAM + Nav2 + RViz2 in Docker
set -e

echo "🤖 Starting G1 SLAM — Simulation Mode (Stage A)"
echo "================================================="

# Allow Docker containers to display GUIs on the host X server
xhost +local:docker

# Build and launch all services
docker compose up --build
