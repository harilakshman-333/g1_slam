"""
Launch file: Start Gazebo simulation with indoor office world,
spawn the G1 robot, and run the ros_gz_bridge for all sensor topics.
"""
import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_gazebo = get_package_share_directory('g1_gazebo')
    pkg_description = get_package_share_directory('g1_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_gazebo, 'worlds', 'indoor_office.sdf')
    bridge_config = os.path.join(pkg_gazebo, 'config', 'gz_bridge.yaml')
    xacro_file = os.path.join(pkg_description, 'urdf', 'g1.urdf.xacro')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use Gazebo simulation clock'
        ),

        # Set Gazebo resource path so it can find our world + models
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(pkg_gazebo, 'worlds') + ':' +
                  os.path.join(pkg_gazebo, 'models')
        ),

        # ── 1. Launch Gazebo server (headless) ──
        # Using ign gazebo directly for Fortress compatibility
        ExecuteProcess(
            cmd=['ign', 'gazebo', '-s', '-r', '--headless-rendering', world_file],
            output='screen',
            additional_env={'IGN_GAZEBO_RESOURCE_PATH': os.path.join(pkg_gazebo, 'worlds')},
        ),

        # ── 2. Robot State Publisher (URDF → /robot_description + TF) ──
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

        # ── 3. Spawn G1 into Gazebo (with delay to let Gazebo initialize) ──
        # Uses -string with xacro output instead of -topic to avoid QoS issues
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    name='spawn_g1',
                    output='screen',
                    arguments=[
                        '-name', 'g1',
                        '-string', Command(['xacro ', xacro_file]),
                        '-world', 'indoor_office',
                        '-x', '0.0',
                        '-y', '0.0',
                        '-z', '0.05',
                    ]
                ),
            ]
        ),

        # ── 4. ros_gz_bridge: Gazebo ↔ ROS2 topic bridging ──
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge',
            output='screen',
            parameters=[{
                'config_file': bridge_config,
                'use_sim_time': use_sim_time,
            }],
        ),

        # ── 5. Static TF: odom → base_footprint fallback ──
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='odom_to_base_footprint_fallback',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_footprint'],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
