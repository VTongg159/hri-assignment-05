"""Launch the Jazzy/Harmonic TurtleBot 4 simulation and RViz."""

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package = FindPackageShare('turtlebot4_yolo_nav')
    simulator = FindPackageShare('nav2_minimal_tb4_sim')
    headless = LaunchConfiguration('headless')
    world = LaunchConfiguration('world')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([simulator, 'launch', 'simulation.launch.py'])
        ),
        launch_arguments={
            'headless': headless,
            'world': world,
            'x_pose': '-3.5',
            'y_pose': '-2.5',
            'yaw': '0.0',
            'use_sim_time': 'true',
            'rviz_config_file': PathJoinSubstitution(
                [package, 'rviz', 'turtlebot4_yolo_nav.rviz']
            ),
        }.items(),
    )

    return LaunchDescription([
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH', PathJoinSubstitution([package, 'models'])
        ),
        DeclareLaunchArgument(
            'headless', default_value='False', choices=['True', 'False']
        ),
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [package, 'worlds', 'hri_lab_yolo.sdf']
            ),
            description='Gazebo Harmonic world file',
        ),
        simulation,
    ])

