# TurtleBot 4 Navigation & YOLO — Lab 05

AMCL localization using the map from Lab 04, autonomous navigation through
three goals with Nav2, and YOLO11n object detection from the robot's RGB camera.

**Platform:** Ubuntu 24.04 · ROS 2 Jazzy · Gazebo Harmonic.

## Installation

Clone the repository:

```bash
git clone https://github.com/VTongg159/hri-assignment-05.git
cd hri-assignment-05
```

With ROS 2 Jazzy installed, run the following from the repository root:

```bash
sudo apt update
sudo apt install -y python3-venv python3-colcon-common-extensions \
  ros-jazzy-nav2-bringup ros-jazzy-nav2-minimal-tb4-sim \
  ros-jazzy-nav2-simple-commander ros-jazzy-cv-bridge \
  ros-jazzy-ros-gz-image ros-jazzy-rviz2

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt

source /opt/ros/jazzy/setup.bash
python -m colcon build --symlink-install --packages-select turtlebot4_yolo_nav
```

Build with `python -m colcon` inside the virtual environment so the YOLO
executable uses the Python interpreter that has Ultralytics installed.
NumPy is restricted to version 1.x for compatibility with Jazzy's `cv_bridge`.

## Run the Demo

In a new terminal, open the repository root and run:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=19

ros2 launch turtlebot4_yolo_nav demo.launch.py
```

The launch file starts **Gazebo, RViz2, YOLO, AMCL, and Nav2**, sets the
initial pose, and navigates through Goal 1 → Goal 2 → Goal 3. No additional
terminals or manual navigation goals are required. Press **Ctrl+C** to stop.

An Internet connection is required if `yolo11n.pt` has not been downloaded.
The map, world, chair and plant meshes, and textures are included in the
package. YOLO displays bounding boxes, class names, and confidence scores;
the terminal reports detections and navigation results.

## Configuration

Goals are defined in `src/turtlebot4_yolo_nav/config/goals.yaml` in the
`map` frame, with positions in meters and yaw in radians:

| Goal | x | y | yaw |
| --- | ---: | ---: | ---: |
| 1 — chair | -0.30 | 3.00 | 0.00 |
| 2 — stop sign | 4.20 | 0.00 | 0.00 |
| 3 — potted plant | 7.20 | 2.00 | 0.00 |

The initial map pose is `(0, 0, 0)`, corresponding to the Gazebo spawn pose
`(-3.5, -2.5, 0)`. Goals are sent sequentially. By default, the mission stops
if a goal fails or exceeds the 180-second timeout.

`config/yolo.yaml` selects `yolo11n.pt`, a confidence threshold of 0.25,
an IoU threshold of 0.45, and a maximum inference rate of 3 Hz on the CPU.
`config/nav2_params.yaml` contains AMCL, planner, controller, and costmap settings.

## Package Structure

```text
src/turtlebot4_yolo_nav/
├── config/                  Nav2, goal, and YOLO parameters
├── launch/                  Demo and component launch files
├── maps/                    map.yaml and map.pgm from Lab 04
├── models/                  Meshes, textures, and ATTRIBUTION.md
├── rviz/                    Map, path, camera, and YOLO displays
├── turtlebot4_yolo_nav/
│   ├── navigate_goals.py     NavigateToPose client using BasicNavigator
│   └── yolo_detector.py      Camera → cv_bridge → YOLO → image/JSON
├── worlds/                  hri_lab_yolo.sdf
└── test/                    Quaternion conversion tests
```

| Interface | Purpose |
| --- | --- |
| `/map`, `/scan`, `/amcl_pose` | Map, LiDAR, and localization |
| `/navigate_to_pose` (action) | Navigation goals, feedback, and results |
| `/plan`, `/cmd_vel` | Planned path and velocity commands |
| `/rgbd_camera/image` | Simulated RGB camera images |
| `/yolo/annotated_image` | Annotated images for RViz |
| `/yolo/detections` | JSON containing classes, confidence scores, and boxes |
| `/navigation_goals` | Goal markers on the map |

## Troubleshooting

- **Package not found:** run all three `source` commands under Run the Demo.
- **No module named ultralytics:** activate `.venv` and rebuild with
  `python -m colcon`.
- **Robot not visible immediately in RViz:** allow the navigation node to set
  the initial pose and AMCL to publish TF. Avoid running another Gazebo/Nav2
  instance in the same ROS domain.
- YOLO may also label the plant's pot as `vase`; predictions depend on the view.

The demo has been tested with all three goals completed while YOLO runs
alongside navigation.

## License and References

Source code: [Apache-2.0](LICENSE). Third-party meshes and textures:
**CC BY 4.0**. See [model attribution and modifications](src/turtlebot4_yolo_nav/models/ATTRIBUTION.md).

- [Nav2 Simple Commander — Jazzy](https://docs.nav2.org/jazzy/configuration_and_development/simple_commander_api/simple_commander_api/)
- [Ultralytics Predict](https://docs.ultralytics.com/modes/predict/)
- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
