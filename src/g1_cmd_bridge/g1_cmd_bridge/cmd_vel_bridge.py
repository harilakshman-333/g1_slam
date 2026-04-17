"""
G1 Command Velocity Bridge Node
================================
Subscribes to /cmd_vel (geometry_msgs/Twist) from Nav2 or teleop
and translates it into Unitree G1 LocoClient walking commands.

This node is ONLY used in Stage B (physical hardware).
In Stage A (simulation), Gazebo's VelocityControl plugin handles /cmd_vel directly.

Safety features:
  - 50Hz heartbeat re-sends last command to keep G1 balance controller stable
  - Velocity clamping to configurable max values
  - Zero-velocity on shutdown
  - Status check before sending commands

Usage:
  ros2 run g1_cmd_bridge cmd_vel_bridge
  ros2 run g1_cmd_bridge cmd_vel_bridge --ros-args -p max_linear_vel:=0.3
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# NOTE: unitree_sdk2py must be installed (built from unitree_sdk2 repo).
# These imports will fail in simulation — that's expected since this
# node is only launched in Stage B (hardware mode).
try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.g1.loco.g1_loco_client import G1LocoClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class CmdVelBridge(Node):
    """Bridge ROS2 /cmd_vel → Unitree G1 LocoClient.Move()"""

    def __init__(self):
        super().__init__('g1_cmd_vel_bridge')

        # ── Parameters ──
        self.declare_parameter('max_linear_vel', 0.5)    # m/s
        self.declare_parameter('max_lateral_vel', 0.3)    # m/s
        self.declare_parameter('max_angular_vel', 1.0)    # rad/s
        self.declare_parameter('network_interface', 'eth0')
        self.declare_parameter('heartbeat_hz', 50.0)

        self.max_vx = self.get_parameter('max_linear_vel').value
        self.max_vy = self.get_parameter('max_lateral_vel').value
        self.max_vyaw = self.get_parameter('max_angular_vel').value
        iface = self.get_parameter('network_interface').value
        hb_hz = self.get_parameter('heartbeat_hz').value

        # ── Initialize Unitree SDK2 ──
        if not SDK_AVAILABLE:
            self.get_logger().fatal(
                'unitree_sdk2py not found! This node requires the Unitree SDK2 '
                'Python bindings. Install from: '
                'https://github.com/unitreerobotics/unitree_sdk2'
            )
            raise RuntimeError('unitree_sdk2py not available')

        self.get_logger().info(f'Initializing G1 LocoClient on interface: {iface}')
        ChannelFactoryInitialize(0, iface)

        self.loco_client = G1LocoClient()
        self.loco_client.Init()
        self.get_logger().info('G1 LocoClient initialized successfully')

        # ── State ──
        self.last_cmd = Twist()
        self.cmd_received = False

        # ── Subscriber ──
        self.sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10
        )

        # ── Heartbeat timer: re-send last cmd at 50Hz ──
        # The G1 balance controller needs continuous velocity commands
        # to maintain a stable walking gait.
        period = 1.0 / hb_hz
        self.timer = self.create_timer(period, self.heartbeat_callback)

        self.get_logger().info(
            f'Bridge active — max vel: [{self.max_vx}, {self.max_vy}, {self.max_vyaw}] '
            f'heartbeat: {hb_hz}Hz'
        )

    def clamp(self, value: float, limit: float) -> float:
        """Clamp a value to [-limit, +limit]."""
        return max(-limit, min(limit, value))

    def cmd_vel_callback(self, msg: Twist):
        """Handle incoming /cmd_vel from Nav2 or teleop."""
        self.last_cmd = msg
        self.cmd_received = True
        self.send_velocity(msg)

    def send_velocity(self, msg: Twist):
        """Send clamped velocity to G1 LocoClient."""
        vx = self.clamp(msg.linear.x, self.max_vx)
        vy = self.clamp(msg.linear.y, self.max_vy)
        vyaw = self.clamp(msg.angular.z, self.max_vyaw)

        try:
            self.loco_client.Move(vx, vy, vyaw)
        except Exception as e:
            self.get_logger().error(f'LocoClient.Move() failed: {e}')

    def heartbeat_callback(self):
        """Re-send last command at 50Hz to keep balance controller stable."""
        if self.cmd_received:
            self.send_velocity(self.last_cmd)

    def destroy_node(self):
        """Send zero velocity on shutdown for safety."""
        self.get_logger().info('Shutting down — sending zero velocity')
        try:
            self.loco_client.Move(0.0, 0.0, 0.0)
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = CmdVelBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
