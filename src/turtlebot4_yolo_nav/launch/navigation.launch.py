"""Start Nav2 planning, control, behavior, and navigator servers."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('turtlebot4_yolo_nav')
    nav2 = FindPackageShare('nav2_bringup')
    params_file = LaunchConfiguration('params_file')

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav2, 'launch', 'navigation_launch.py'])
        ),
        launch_arguments={
            'params_file': params_file,
            'use_sim_time': 'true',
            'autostart': 'true',
            'use_composition': 'False',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([package, 'config', 'nav2_params.yaml']),
        ),
        navigation,
    ])

