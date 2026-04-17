"""
Launch file: SLAM pipeline for Unitree G1.
  1. pointcloud_to_laserscan — converts 3D LiDAR PointCloud2 → 2D LaserScan
  2. slam_toolbox — online async SLAM using the 2D scan
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_dir = get_package_share_directory('g1_slam')
    slam_params = os.path.join(pkg_dir, 'config', 'slam_toolbox.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock (true for Gazebo, false for hardware)'
        ),

        # ── 1. Convert 3D PointCloud2 → 2D LaserScan ──
        # Takes a horizontal z-slice of the 3D cloud at ~hip height
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'min_height': 0.1,          # Min z relative to sensor frame
                'max_height': 1.5,          # Max z relative to sensor frame
                'angle_min': -3.14159,      # Full 360°
                'angle_max': 3.14159,
                'angle_increment': 0.00349, # ~0.2° resolution → 1800 beams
                'scan_time': 0.1,           # 10 Hz
                'range_min': 0.1,
                'range_max': 40.0,
                'target_frame': 'base_footprint',
                'inf_epsilon': 1.0,
                'use_inf': True,
            }],
            remappings=[
                ('cloud_in', '/lidar/points'),
                ('scan', '/scan'),
            ]
        ),

        # ── 2. slam_toolbox: Online Async SLAM ──
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_params,
                {'use_sim_time': use_sim_time},
            ],
        ),
    ])
