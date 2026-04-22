FROM osrf/ros:humble-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ARG ENABLE_HW_STACK=0

# ── Core ROS2 packages for SLAM + Navigation ──
RUN apt-get update && apt-get install -y --fix-missing \
    ros-humble-slam-toolbox \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-pcl-ros \
    ros-humble-pointcloud-to-laserscan \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-xacro \
    ros-humble-tf2-tools \
    ros-humble-teleop-twist-keyboard \
    ros-humble-ros-gz \
    ros-humble-ros-gz-bridge \
    ros-humble-ros-gz-sim \
    ros-humble-ros-gz-interfaces \
    ros-humble-realsense2-camera \
    ros-humble-realsense2-description \
    ros-humble-rosidl-generator-dds-idl \
    libyaml-cpp-dev \
    libeigen3-dev git cmake build-essential \
    python3-pip python3-colcon-common-extensions \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /g1_ws/src && cd /g1_ws/src && \
    git clone https://github.com/unitreerobotics/unitree_ros.git --depth 1 && \
    git clone https://github.com/unitreerobotics/unitree_ros2.git /tmp/unitree_ros2 --depth 1 && \
    mv /tmp/unitree_ros2/cyclonedds_ws/src/unitree ./unitree_ros2_msgs && \
    rm -rf /tmp/unitree_ros2

# ══════════════════════════════════════════════════════════════
# STAGE B DEPENDENCIES (hardware only — not needed for simulation)
# Uncomment these blocks when moving to physical G1 hardware.
# ══════════════════════════════════════════════════════════════

# ── Unitree SDK2 (Stage B: G1 hardware communication) ──
WORKDIR /opt
RUN if [ "$ENABLE_HW_STACK" = "1" ]; then \
      git clone https://github.com/unitreerobotics/unitree_sdk2.git && \
      cd unitree_sdk2 && mkdir build && cd build && \
      cmake .. -DCMAKE_BUILD_TYPE=Release && \
      make -j$(nproc) && make install; \
    fi

# ── Livox SDK2 + ROS2 driver (Stage B: real Livox Mid-360 LiDAR) ──
# Must install Livox-SDK2 first, then use build.sh (not colcon directly)
RUN if [ "$ENABLE_HW_STACK" = "1" ]; then \
      git clone https://github.com/Livox-SDK/Livox-SDK2.git /opt/Livox-SDK2 && \
      cd /opt/Livox-SDK2 && mkdir build && cd build && \
      cmake .. -DCMAKE_BUILD_TYPE=Release && \
      make -j$(nproc) && make install; \
    fi

RUN if [ "$ENABLE_HW_STACK" = "1" ]; then \
      mkdir -p /livox_ws/src && cd /livox_ws/src && \
      git clone https://github.com/Livox-SDK/livox_ros_driver2.git --depth 1 && \
      cd /livox_ws/src/livox_ros_driver2 && \
      ./build.sh humble; \
    fi

# ── Fast-LIO2 (Stage B: LiDAR-Inertial Odometry) ──
RUN if [ "$ENABLE_HW_STACK" = "1" ]; then \
      mkdir -p /fastlio_ws/src && cd /fastlio_ws/src && \
      git clone https://github.com/hku-mars/FAST_LIO.git --recursive && \
      cd /fastlio_ws && \
      bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"; \
    fi

# ── G1 SLAM workspace ──
RUN mkdir -p /g1_ws/src /g1_ws/maps
WORKDIR /g1_ws

# Entrypoint sources all workspaces
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
