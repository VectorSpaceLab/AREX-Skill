#!/usr/bin/env python3
"""Operator-controlled CycloneDDS-to-FastDDS Go2 state bridge.

Default invocation is a dry-run that prints the selected transport settings.
Use --run only on the Jetson after ROS 2 Humble, Unitree messages, both RMW
implementations, and robot/network authorization are already in place.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
from typing import Any

MOTOR_JOINT_NAMES = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]


def cyclone_uri(interface: str) -> str:
    return f"<CycloneDDS><Domain><General><NetworkInterfaceAddress>{interface}</NetworkInterfaceAddress></General></Domain></CycloneDDS>"


def cyclone_reader(queue: mp.Queue, interface: str) -> None:
    os.environ["RMW_IMPLEMENTATION"] = "rmw_cyclonedds_cpp"
    os.environ["CYCLONEDDS_URI"] = cyclone_uri(interface)
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from unitree_go.msg import LowState

    qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=10)

    class Reader(Node):
        def __init__(self) -> None:
            super().__init__("twinbot_reader")
            self._count = 0
            self.create_subscription(LowState, "/lowstate", self._callback, qos)
            self.get_logger().info(f"CycloneDDS reader on {interface} — listening /lowstate")

        def _callback(self, msg: Any) -> None:
            pos = [float(msg.motor_state[i].q) for i in range(12)]
            vel = [float(msg.motor_state[i].dq) for i in range(12)]
            effort = [float(msg.motor_state[i].tau_est) for i in range(12)]
            q = msg.imu_state.quaternion
            quat = [float(q[i]) for i in range(4)]
            gyro = [float(value) for value in msg.imu_state.gyroscope]
            try:
                queue.put_nowait((pos, vel, effort, quat, gyro))
            except Exception:
                pass
            self._count += 1
            if self._count % 1000 == 0:
                self.get_logger().info(f"forwarded {self._count} messages — FL_hip={pos[3]:.3f} rad")

    rclpy.init()
    node = Reader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def fastdds_publisher(queue: mp.Queue) -> None:
    os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"
    os.environ.pop("CYCLONEDDS_URI", None)
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from sensor_msgs.msg import JointState

    qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)

    class Publisher(Node):
        def __init__(self) -> None:
            super().__init__("twinbot_publisher")
            self._joint_pub = self.create_publisher(JointState, "/real_dog/joint_states", qos)
            self._odom_pub = self.create_publisher(Odometry, "/real_dog/odom", 10)
            self.create_timer(0.002, self._drain)

        def _drain(self) -> None:
            latest = None
            while True:
                try:
                    latest = queue.get_nowait()
                except Exception:
                    break
            if latest is None:
                return
            pos, vel, effort, quat, gyro = latest
            stamp = self.get_clock().now().to_msg()
            joint = JointState()
            joint.header.stamp = stamp
            joint.header.frame_id = "base_link"
            joint.name = MOTOR_JOINT_NAMES
            joint.position, joint.velocity, joint.effort = pos, vel, effort
            self._joint_pub.publish(joint)
            odom = Odometry()
            odom.header.stamp = stamp
            odom.header.frame_id = "odom"
            odom.child_frame_id = "base_link"
            odom.pose.pose.orientation.w = quat[0]
            odom.pose.pose.orientation.x = quat[1]
            odom.pose.pose.orientation.y = quat[2]
            odom.pose.pose.orientation.z = quat[3]
            odom.twist.twist.angular.x, odom.twist.twist.angular.y, odom.twist.twist.angular.z = gyro
            self._odom_pub.publish(odom)

    rclpy.init()
    node = Publisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Start both live ROS processes; omitted means dry-run")
    parser.add_argument("--ethernet-interface", default="enP8p1s0", help="Jetson interface for CycloneDDS LowState")
    parser.add_argument("--queue-size", type=int, default=5, help="Maximum cross-process state queue size")
    args = parser.parse_args()
    if args.queue_size < 1:
        parser.error("--queue-size must be positive")
    print(f"ethernet_interface={args.ethernet_interface}")
    print("cyclone_uri=" + cyclone_uri(args.ethernet_interface))
    print("joint_count=12")
    if not args.run:
        print("dry_run=true; pass --run only on an authorized Jetson ROS 2 host")
        return 0
    queue: mp.Queue = mp.Queue(maxsize=args.queue_size)
    reader = mp.Process(target=cyclone_reader, args=(queue, args.ethernet_interface), daemon=True)
    writer = mp.Process(target=fastdds_publisher, args=(queue,), daemon=True)
    reader.start()
    writer.start()
    print(f"reader_pid={reader.pid} publisher_pid={writer.pid}", flush=True)
    try:
        reader.join()
    except KeyboardInterrupt:
        pass
    finally:
        reader.terminate()
        writer.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
