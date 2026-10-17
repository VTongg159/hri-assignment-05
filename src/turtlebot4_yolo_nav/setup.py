from glob import glob
import os
from pathlib import Path

from setuptools import find_packages, setup


package_name = 'turtlebot4_yolo_nav'

model_data = [
    (str(Path('share') / package_name / directory),
     [str(path) for path in sorted(Path(directory).iterdir()) if path.is_file()])
    for directory, _, filenames in sorted(os.walk('models')) if filenames
]

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        *model_data,
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Nguyen Van Tong',
    maintainer_email='vantongg159@gmail.com',
    description='TurtleBot 4 localization, autonomous navigation, and YOLO detection.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'navigate_goals = turtlebot4_yolo_nav.navigate_goals:main',
            'yolo_detector = turtlebot4_yolo_nav.yolo_detector:main',
        ],
    },
)

