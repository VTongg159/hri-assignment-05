"""Send three sequential NavigateToPose goals with Nav2 Simple Commander."""

import math
import time

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.duration import Duration
from rclpy.qos import DurabilityPolicy, QoSProfile
from visualization_msgs.msg import Marker, MarkerArray


def yaw_to_quaternion(yaw):
    """Return the planar quaternion components for a yaw angle."""
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def make_pose(navigator, x, y, yaw):
    """Build a map-frame PoseStamped using the current ROS clock."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z, pose.pose.orientation.w = yaw_to_quaternion(float(yaw))
    return pose


def publish_goal_markers(navigator, goals, names):
    """Publish arrows and labels so all configured goals are visible in RViz."""
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    publisher = navigator.create_publisher(MarkerArray, '/navigation_goals', qos)
    markers = MarkerArray()
    now = navigator.get_clock().now().to_msg()

    for index, ((x, y, yaw), name) in enumerate(zip(goals, names), start=1):
        arrow = Marker()
        arrow.header.frame_id = 'map'
        arrow.header.stamp = now
        arrow.ns = 'goal_arrows'
        arrow.id = index
        arrow.type = Marker.ARROW
        arrow.action = Marker.ADD
        arrow.pose = make_pose(navigator, x, y, yaw).pose
        arrow.scale.x = 0.65
        arrow.scale.y = 0.12
        arrow.scale.z = 0.12
        arrow.color.r = 0.1
        arrow.color.g = 0.85
        arrow.color.b = 0.2
        arrow.color.a = 1.0
        markers.markers.append(arrow)

        label = Marker()
        label.header.frame_id = 'map'
        label.header.stamp = now
        label.ns = 'goal_labels'
        label.id = 100 + index
        label.type = Marker.TEXT_VIEW_FACING
        label.action = Marker.ADD
        label.pose.position.x = float(x)
        label.pose.position.y = float(y)
        label.pose.position.z = 0.55
        label.pose.orientation.w = 1.0
        label.scale.z = 0.28
        label.color.r = 1.0
        label.color.g = 0.9
        label.color.b = 0.1
        label.color.a = 1.0
        label.text = name
        markers.markers.append(label)

    # Transient-local QoS retains this single publication for late RViz subscribers.
    publisher.publish(markers)
    return publisher


def read_configuration(navigator):
    """Declare, validate, and return mission parameters."""
    navigator.declare_parameter('set_initial_pose', True)
    navigator.declare_parameter('initial_pose', [0.0, 0.0, 0.0])
    navigator.declare_parameter(
        'goals', [-0.3, 3.0, 0.0, 4.2, 0.0, 0.0, 7.2, 2.0, 0.0]
    )
    navigator.declare_parameter(
        'goal_names', ['Goal 1', 'Goal 2', 'Goal 3']
    )
    navigator.declare_parameter('goal_timeout', 180.0)
    navigator.declare_parameter('feedback_period', 2.0)
    navigator.declare_parameter('stop_on_failure', True)

    initial = list(navigator.get_parameter('initial_pose').value)
    flat_goals = list(navigator.get_parameter('goals').value)
    names = list(navigator.get_parameter('goal_names').value)
    if len(initial) != 3:
        raise ValueError('initial_pose must contain exactly [x, y, yaw]')
    if not flat_goals or len(flat_goals) % 3 != 0:
        raise ValueError('goals must contain one or more [x, y, yaw] triples')

    goals = [tuple(flat_goals[i:i + 3]) for i in range(0, len(flat_goals), 3)]
    if len(names) != len(goals):
        names = [f'Goal {i}' for i in range(1, len(goals) + 1)]
    return initial, goals, names


def navigate_one_goal(navigator, pose, name, timeout, feedback_period):
    """Navigate to one pose, periodically reporting distance and elapsed time."""
    navigator.get_logger().info(
        f'Sending {name}: x={pose.pose.position.x:.2f}, '
        f'y={pose.pose.position.y:.2f}'
    )
    if navigator.goToPose(pose) is False:
        navigator.get_logger().error(f'{name} was rejected by Nav2')
        return TaskResult.FAILED

    started = time.monotonic()
    last_report = -feedback_period
    while not navigator.isTaskComplete():
        elapsed = time.monotonic() - started
        if elapsed >= timeout:
            navigator.get_logger().error(
                f'{name} exceeded {timeout:.0f} s; canceling the goal'
            )
            navigator.cancelTask()
            return TaskResult.CANCELED

        feedback = navigator.getFeedback()
        if feedback is not None and elapsed - last_report >= feedback_period:
            last_report = elapsed
            distance = getattr(feedback, 'distance_remaining', float('nan'))
            nav_time_msg = getattr(feedback, 'navigation_time', None)
            nav_seconds = (
                Duration.from_msg(nav_time_msg).nanoseconds / 1e9
                if nav_time_msg is not None else elapsed
            )
            navigator.get_logger().info(
                f'{name}: remaining={distance:.2f} m, time={nav_seconds:.1f} s'
            )

    return navigator.getResult()


def main(args=None):
    """Run the configured sequential navigation mission."""
    rclpy.init(args=args)
    navigator = BasicNavigator(node_name='navigate_goals')
    exit_code = 0

    try:
        initial, goals, names = read_configuration(navigator)
        timeout = float(navigator.get_parameter('goal_timeout').value)
        feedback_period = float(navigator.get_parameter('feedback_period').value)
        stop_on_failure = bool(navigator.get_parameter('stop_on_failure').value)

        publish_goal_markers(navigator, goals, names)
        if navigator.get_parameter('set_initial_pose').value:
            navigator.get_logger().info(
                'Publishing initial pose: '
                f'x={initial[0]:.2f}, y={initial[1]:.2f}, yaw={initial[2]:.2f}'
            )
            navigator.setInitialPose(make_pose(navigator, *initial))
        else:
            navigator.get_logger().info(
                'Waiting for an initial pose from RViz / AMCL...'
            )

        navigator.get_logger().info('Waiting until AMCL and Nav2 are active...')
        navigator.waitUntilNav2Active()

        succeeded = 0
        for goal, name in zip(goals, names):
            result = navigate_one_goal(
                navigator,
                make_pose(navigator, *goal),
                name,
                timeout,
                feedback_period,
            )
            if result == TaskResult.SUCCEEDED:
                succeeded += 1
                navigator.get_logger().info(f'{name}: SUCCEEDED')
            elif result == TaskResult.CANCELED:
                navigator.get_logger().warning(f'{name}: CANCELED')
                exit_code = 2
            else:
                navigator.get_logger().error(f'{name}: FAILED ({result.name})')
                exit_code = 1

            if result != TaskResult.SUCCEEDED and stop_on_failure:
                navigator.get_logger().error(
                    'Mission stopped because stop_on_failure=true'
                )
                break

        navigator.get_logger().info(
            f'Mission complete: {succeeded}/{len(goals)} goals succeeded'
        )
    except KeyboardInterrupt:
        navigator.get_logger().warning('Navigation interrupted by user')
        navigator.cancelTask()
        exit_code = 130
    except Exception as exc:  # Keep a clear terminal error for lab debugging.
        navigator.get_logger().error(f'Navigation node error: {exc}')
        exit_code = 1
    finally:
        navigator.destroyNode()
        if rclpy.ok():
            rclpy.shutdown()

    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
