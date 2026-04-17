#!/bin/bash
# Launch keyboard teleop for manual map building
# Use inside a running docker compose session:
#   docker compose exec slam bash /g1_ws/scripts/teleop.sh
set -e

echo "🎮 Keyboard Teleop for G1"
echo "========================="
echo "Use WASD keys to move, Q/E to rotate."
echo ""

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args -p speed:=0.3 -p turn:=0.5
