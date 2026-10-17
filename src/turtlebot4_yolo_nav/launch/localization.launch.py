"""Load the saved map and start Nav2 AMCL."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('turtlebot4_yolo_nav')
    nav2 = FindPackageShare('nav2_bringup')
    map_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav2, 'launch', 'localization_launch.py'])
        ),
        launch_arguments={
            'map': map_file,
            'params_file': params_file,
            'use_sim_time': 'true',
            'autostart': 'true',
            'use_composition': 'False',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=PathJoinSubstitution([package, 'maps', 'map.yaml']),
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([package, 'config', 'nav2_params.yaml']),
        ),
        localization,
    ])

