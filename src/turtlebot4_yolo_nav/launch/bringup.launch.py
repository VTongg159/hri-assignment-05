"""Start simulation, localization, and navigation without the student nodes."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('turtlebot4_yolo_nav')
    headless = LaunchConfiguration('headless')
    return LaunchDescription([
        DeclareLaunchArgument(
            'headless', default_value='False', choices=['True', 'False']
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package, 'launch', 'simulation.launch.py'])
            ),
            launch_arguments={'headless': headless}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package, 'launch', 'localization.launch.py'])
            )
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package, 'launch', 'navigation.launch.py'])
            )
        ),
    ])

