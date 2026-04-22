#!/bin/bash
set -e

# Source ROS2 Humble
source /opt/ros/humble/setup.bash

# Source dependency workspaces (may not exist during first build)
source /livox_ws/install/setup.bash 2>/dev/null || true
source /fastlio_ws/install/setup.bash 2>/dev/null || true

# Source G1 workspace (may not exist until first colcon build)
if [ -f /g1_ws/install/setup.bash ]; then
    source /g1_ws/install/setup.bash
fi

# Ensure CycloneDDS is active
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Apply CycloneDDS config if present (Stage B hardware)
if [ -f /g1_ws/docker/cyclone_dds.xml ]; then
    export CYCLONEDDS_URI=file:///g1_ws/docker/cyclone_dds.xml
fi

# Force software rendering for headless GPU LiDAR sensor (ogre2 needs OpenGL)
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export OGRE_RTT_MODE=Copy

exec "$@"
