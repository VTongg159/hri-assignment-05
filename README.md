# Bài thực hành 05 — TurtleBot 4 Navigation & YOLO

Nguyễn Văn Tổng · 23020766 · K68E-RE

TurtleBot 4 định vị bằng AMCL trên bản đồ tuần 4, tự đi lần lượt qua ba goal
bằng Nav2 và nhận diện vật thể bằng YOLO11n trong khi di chuyển.

Môi trường: **Ubuntu 24.04 · ROS 2 Jazzy · Gazebo Harmonic**.

## Cài đặt một lần

Clone repo:

```bash
git clone https://github.com/VTongg159/hri-assignment-05.git
cd hri-assignment-05
```

Máy đã có ROS 2 Jazzy. Trong thư mục gốc repo, cài các dependency:

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

Build bằng `python -m colcon` trong virtual environment để node YOLO dùng đúng
Python đã cài Ultralytics. NumPy được giới hạn dưới 2 để tương thích
`cv_bridge` của Jazzy.

## Chạy demo

Trong mỗi terminal mới, vào thư mục gốc repo rồi chạy:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=19

ros2 launch turtlebot4_yolo_nav demo.launch.py
```

Một lệnh launch mở **Gazebo, RViz2, camera YOLO, AMCL và Nav2**, tự đặt initial
pose rồi điều khiển robot qua Goal 1 → Goal 2 → Goal 3. Không cần mở thêm
terminal hoặc đặt goal bằng chuột. Nhấn **Ctrl+C** tại terminal để dừng tất cả.

Lần đầu cần Internet để tải `yolo11n.pt`. Mesh ghế/cây, texture, world và map
đã nằm trong package. Khi chạy, YOLO hiển thị bounding box, tên lớp và
confidence; terminal in kết quả từng goal và vật thể phát hiện được.

## Cấu hình

Các tọa độ trong `src/turtlebot4_yolo_nav/config/goals.yaml` thuộc frame
`map`, đơn vị mét và radian:

| Goal | x | y | yaw |
| --- | ---: | ---: | ---: |
| 1 — ghế | -0.30 | 3.00 | 0.00 |
| 2 — biển báo | 4.20 | 0.00 | 0.00 |
| 3 — chậu cây | 7.20 | 2.00 | 0.00 |

Initial pose trong map là `(0, 0, 0)`, tương ứng vị trí spawn
`(-3.5, -2.5, 0)` trong Gazebo. Goal được gửi tuần tự; mặc định nhiệm vụ dừng
nếu một goal thất bại hoặc vượt timeout 180 giây.

`config/yolo.yaml` chọn model `yolo11n.pt`, confidence 0.25, IoU 0.45 và
inference tối đa 3 Hz trên CPU. `config/nav2_params.yaml` chứa cấu hình AMCL,
planner, controller và costmap.

## Cấu trúc mã nguồn

```text
src/turtlebot4_yolo_nav/
├── config/                  Tham số Nav2, goal và YOLO
├── launch/                  Demo và các launch thành phần
├── maps/                    map.yaml, map.pgm từ tuần 4
├── models/                  Mesh, texture và ATTRIBUTION.md
├── rviz/                    Cấu hình hiển thị map, path, camera, YOLO
├── turtlebot4_yolo_nav/
│   ├── navigate_goals.py     Gửi NavigateToPose bằng BasicNavigator
│   └── yolo_detector.py      Camera → cv_bridge → YOLO → ảnh/JSON
├── worlds/                  World hri_lab_yolo.sdf
└── test/                    Kiểm tra hàm tạo quaternion
```

| Giao diện | Vai trò |
| --- | --- |
| `/map`, `/scan`, `/amcl_pose` | Bản đồ, LiDAR và định vị |
| `/navigate_to_pose` (action) | Nhận goal và trả feedback/kết quả |
| `/plan`, `/cmd_vel` | Đường đi và lệnh vận tốc |
| `/rgbd_camera/image` | Ảnh camera RGB mô phỏng |
| `/yolo/annotated_image` | Ảnh đã vẽ box để xem trong RViz |
| `/yolo/detections` | JSON gồm class, confidence và tọa độ box |
| `/navigation_goals` | Marker ba goal trên bản đồ |

## Lưu ý

- `Package not found`: chạy đủ ba lệnh `source` ở mục Chạy demo.
- `No module named ultralytics`: activate `.venv` và build lại bằng
  `python -m colcon`.
- Robot chưa hiện ngay khi mở RViz: chờ node điều hướng đặt initial pose và
  AMCL tạo TF. Không chạy thêm một bản Gazebo/Nav2 khác cùng ROS domain.
- YOLO có thể nhận thêm `vase` ở phần chậu; nhãn phụ thuộc góc nhìn.
- Đã kiểm thử robot hoàn thành 3/3 goal với YOLO chạy song song.

## Giấy phép và tài liệu

Mã nguồn: [Apache-2.0](LICENSE). Mesh/texture bên thứ ba: **CC BY 4.0**;
xem [nguồn model và các thay đổi](src/turtlebot4_yolo_nav/models/ATTRIBUTION.md).

- [Nav2 Simple Commander — Jazzy](https://docs.nav2.org/jazzy/configuration_and_development/simple_commander_api/simple_commander_api/)
- [Ultralytics Predict](https://docs.ultralytics.com/modes/predict/)
- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
