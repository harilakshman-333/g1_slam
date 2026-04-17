#!/bin/bash
# Start Stage B — Physical G1 Hardware
# Uses hardware override compose file
set -e

echo "🤖 Starting G1 SLAM — Hardware Mode (Stage B)"
echo "==============================================="
echo "⚠️  SAFETY: Ensure the G1 is in a harness and the area is clear."
echo "⚠️  SAFETY: Keep the Unitree remote controller nearby."
echo ""

# Allow Docker containers to display GUIs on the host X server
xhost +local:docker

# Build and launch with hardware override
docker compose -f docker-compose.yml -f docker-compose.hw.yml up --build
