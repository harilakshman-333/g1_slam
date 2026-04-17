"""
Launch file: Stage B — Hardware bringup for Unitree G1 Dex3.
Launches real sensor drivers and the cmd_vel bridge.

Replaces the Gazebo simulation (sim.launch.py) in hardware mode.
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_bringup = get_package_share_directory('g1_bringup')
    pkg_description = get_package_share_directory('g1_description')

    xacro_file = os.path.join(pkg_description, 'urdf', 'g1.urdf.xacro')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Must be false for real hardware'
        ),

        # ── 1. Robot State Publisher (URDF → TF) ──
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': ParameterValue(
                    Command(['xacro ', xacro_file]), value_type=str
                ),
                'use_sim_time': use_sim_time,
            }]
        ),

        # ── 2. Livox Mid-360 LiDAR driver ──
        # NOTE: Ensure livox_ros_driver2 is built and the MID360_config.json
        # has the correct host_ip and LiDAR IP for your setup.
        # The driver publishes:
        #   /livox/lidar  (PointCloud2)
        #   /livox/imu    (Imu)
        #
        # Uncomment and configure when ready:
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(
        #         os.path.join(
        #             get_package_share_directory('livox_ros_driver2'),
        #             'launch', 'msg_MID360_launch.py'
        #         )
        #     ),
        # ),

        # ── 3. Intel RealSense D435i camera ──
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense2_camera',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'enable_color': True,
                'enable_depth': True,
                'enable_infra1': False,
                'enable_infra2': False,
                'depth_module.profile': '640x480x30',
                'rgb_camera.profile': '640x480x30',
                'enable_gyro': True,
                'enable_accel': True,
            }],
        ),

        # ── 4. G1 cmd_vel bridge (Nav2 → LocoClient) ──
        Node(
            package='g1_cmd_bridge',
            executable='cmd_vel_bridge',
            name='g1_cmd_vel_bridge',
            output='screen',
            parameters=[{
                'max_linear_vel': 0.3,      # Start conservative!
                'max_lateral_vel': 0.2,
                'max_angular_vel': 0.5,
                'network_interface': 'eth0',
                'heartbeat_hz': 50.0,
            }],
        ),

        # ── 5. Static TF: map → odom (will be overridden by SLAM) ──
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_init',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
