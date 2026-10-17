"""One-command demo: simulation + AMCL + Nav2 + YOLO + three-goal mission."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('turtlebot4_yolo_nav')
    headless = LaunchConfiguration('headless')
    show_window = LaunchConfiguration('show_window')

    core = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([package, 'launch', 'bringup.launch.py'])
        ),
        launch_arguments={'headless': headless}.items(),
    )
    detector = TimerAction(
        period=3.0,
        actions=[Node(
            package='turtlebot4_yolo_nav',
            executable='yolo_detector',
            name='yolo_detector',
            output='screen',
            parameters=[
                PathJoinSubstitution([package, 'config', 'yolo.yaml']),
                {'show_window': show_window},
            ],
        )],
    )
    mission = TimerAction(
        period=8.0,
        actions=[Node(
            package='turtlebot4_yolo_nav',
            executable='navigate_goals',
            name='navigate_goals',
            output='screen',
            parameters=[PathJoinSubstitution([package, 'config', 'goals.yaml'])],
        )],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless', default_value='False', choices=['True', 'False']
        ),
        DeclareLaunchArgument(
            'show_window', default_value='True', choices=['True', 'False']
        ),
        core,
        detector,
        mission,
    ])
