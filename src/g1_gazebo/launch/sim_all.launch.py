"""
Master launch file: Runs the entire Stage A simulation pipeline in one process.
  - Gazebo server (headless) with indoor office world
  - Robot State Publisher (URDF → TF)
  - G1 spawn into Gazebo
  - ros_gz_bridge (all sensor/cmd topics)
  - pointcloud_to_laserscan + slam_toolbox
  - Nav2 full stack
  - Static TF fallbacks
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
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_gazebo = get_package_share_directory('g1_gazebo')
    pkg_description = get_package_share_directory('g1_description')
    pkg_slam = get_package_share_directory('g1_slam')
    pkg_navigation = get_package_share_directory('g1_navigation')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    world_file = os.path.join(pkg_gazebo, 'worlds', 'indoor_office.sdf')
    bridge_config = os.path.join(pkg_gazebo, 'config', 'gz_bridge.yaml')
    xacro_file = os.path.join(pkg_description, 'urdf', 'g1.urdf.xacro')
    slam_params = os.path.join(pkg_slam, 'config', 'slam_toolbox.yaml')
    nav2_params = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use Gazebo simulation clock'
        ),

        # ── ENV: Gazebo resource path ──
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(pkg_gazebo, 'worlds') + ':' +
                  os.path.join(pkg_gazebo, 'models')
        ),

        # ════════════════════════════════════════════
        # 1. GAZEBO SERVER (headless with xvfb virtual display)
        # ════════════════════════════════════════════
        ExecuteProcess(
            cmd=['xvfb-run', '-a', 'ign', 'gazebo', '-s', '-r', world_file],
            output='screen',
            additional_env={
                'IGN_GAZEBO_RESOURCE_PATH': os.path.join(pkg_gazebo, 'worlds'),
            },
        ),

        # ════════════════════════════════════════════
        # 2. ROBOT STATE PUBLISHER
        # ════════════════════════════════════════════
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

        # ════════════════════════════════════════════
        # 3. SPAWN G1 (after 5s delay for Gazebo init)
        # ════════════════════════════════════════════
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
                        '-x', '0.0', '-y', '0.0', '-z', '0.05',
                    ]
                ),
            ]
        ),

        # ════════════════════════════════════════════
        # 4. ROS_GZ_BRIDGE (command-line args for Fortress)
        #    Format: /gz_topic@ros_type[ignition_type  (GZ→ROS)
        #            /gz_topic@ros_type]ignition_type  (ROS→GZ)
        # ════════════════════════════════════════════
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            output='screen',
            arguments=[
                # Clock (CRITICAL for use_sim_time)
                '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
                # LiDAR scan directly
                '/lidar/points@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
                # RGB camera
                '/camera/color/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image',
                # Depth camera
                '/camera/depth/image_rect_raw@sensor_msgs/msg/Image[ignition.msgs.Image',
                # Velocity commands (ROS -> GZ)
                '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
                # Odometry
                '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            ],
            remappings=[
                ('/lidar/points', '/scan'),
            ]
        ),

        # ════════════════════════════════════════════
        # 5. STATIC TF: odom → base_footprint fallback
        # ════════════════════════════════════════════
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='odom_to_base_footprint',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_footprint'],
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        # ════════════════════════════════════════════
        # 6. SLAM: slam_toolbox
        #    (delayed 8s to let Gazebo + sensors start)
        # ════════════════════════════════════════════
        TimerAction(
            period=8.0,
            actions=[
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
            ]
        ),

        # ════════════════════════════════════════════
        # 7. NAV2 (delayed 12s to let SLAM initialize)
        # ════════════════════════════════════════════
        TimerAction(
            period=12.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
                    ),
                    launch_arguments={
                        'use_sim_time': 'true',
                        'params_file': nav2_params,
                        'autostart': 'true',
                    }.items(),
                ),
            ]
        ),
    ])
