"""Run Ultralytics YOLO on a ROS 2 RGB image stream."""

import json
import os
import time

import cv2
from cv_bridge import CvBridge, CvBridgeError
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String


class YoloDetector(Node):
    """Subscribe to camera images, detect objects, and publish annotations."""

    def __init__(self):
        super().__init__('yolo_detector')
        self.declare_parameter('image_topic', '/rgbd_camera/image')
        self.declare_parameter('annotated_topic', '/yolo/annotated_image')
        self.declare_parameter('detections_topic', '/yolo/detections')
        self.declare_parameter('model', 'yolo11n.pt')
        self.declare_parameter('confidence', 0.25)
        self.declare_parameter('iou', 0.45)
        self.declare_parameter('image_size', 640)
        self.declare_parameter('inference_hz', 3.0)
        self.declare_parameter('device', 'cpu')
        self.declare_parameter('show_window', True)
        self.declare_parameter('log_interval', 1.0)

        image_topic = str(self.get_parameter('image_topic').value)
        annotated_topic = str(self.get_parameter('annotated_topic').value)
        detections_topic = str(self.get_parameter('detections_topic').value)
        model_path = str(self.get_parameter('model').value)

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                'Missing ultralytics. Activate the project virtual environment '
                'or run the installation command in README.md.'
            ) from exc

        self.get_logger().info(f'Loading YOLO model: {model_path}')
        self.model = YOLO(model_path)
        self.bridge = CvBridge()
        self.confidence = float(self.get_parameter('confidence').value)
        self.iou = float(self.get_parameter('iou').value)
        self.image_size = int(self.get_parameter('image_size').value)
        self.device = str(self.get_parameter('device').value)
        self.show_window = bool(self.get_parameter('show_window').value)
        self.inference_period = 1.0 / max(
            0.1, float(self.get_parameter('inference_hz').value)
        )
        self.log_interval = max(0.0, float(self.get_parameter('log_interval').value))
        self.last_inference = 0.0
        self.last_log = 0.0
        self.window_available = bool(
            os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        )

        self.annotated_publisher = self.create_publisher(Image, annotated_topic, 10)
        self.detections_publisher = self.create_publisher(String, detections_topic, 10)
        self.subscription = self.create_subscription(
            Image, image_topic, self.image_callback, qos_profile_sensor_data
        )
        self.get_logger().info(
            f'YOLO ready: {image_topic} -> {annotated_topic}, '
            f'confidence={self.confidence:.2f}, rate={1.0 / self.inference_period:.1f} Hz'
        )
        if self.show_window and not self.window_available:
            self.get_logger().warning(
                'show_window=true but no graphical display was found; '
                'annotated images will still be published.'
            )

    def image_callback(self, message):
        """Throttle and process the newest camera frame."""
        now = time.monotonic()
        if now - self.last_inference < self.inference_period:
            return
        self.last_inference = now

        try:
            frame = self.bridge.imgmsg_to_cv2(message, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'cv_bridge input conversion failed: {exc}')
            return

        try:
            result = self.model.predict(
                source=frame,
                conf=self.confidence,
                iou=self.iou,
                imgsz=self.image_size,
                device=self.device,
                verbose=False,
            )[0]
        except Exception as exc:
            self.get_logger().error(f'YOLO inference failed: {exc}')
            return

        detections = []
        if result.boxes is not None:
            coordinates = result.boxes.xyxy.cpu().tolist()
            confidences = result.boxes.conf.cpu().tolist()
            classes = result.boxes.cls.cpu().tolist()
            for xyxy, confidence, class_id in zip(coordinates, confidences, classes):
                class_index = int(class_id)
                detections.append({
                    'class_id': class_index,
                    'class_name': str(result.names[class_index]),
                    'confidence': round(float(confidence), 4),
                    'bbox_xyxy': [round(float(value), 1) for value in xyxy],
                })

        annotated = result.plot()
        try:
            annotated_message = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            annotated_message.header = message.header
            self.annotated_publisher.publish(annotated_message)
        except CvBridgeError as exc:
            self.get_logger().error(f'cv_bridge output conversion failed: {exc}')

        detection_message = String()
        detection_message.data = json.dumps({
            'stamp': {
                'sec': message.header.stamp.sec,
                'nanosec': message.header.stamp.nanosec,
            },
            'frame_id': message.header.frame_id,
            'count': len(detections),
            'detections': detections,
        })
        self.detections_publisher.publish(detection_message)

        if now - self.last_log >= self.log_interval:
            self.last_log = now
            if detections:
                summary = ', '.join(
                    f"{item['class_name']} {item['confidence']:.2f}"
                    for item in detections
                )
                self.get_logger().info(f'Detected {len(detections)} object(s): {summary}')
            else:
                self.get_logger().info('Detected 0 objects')

        if self.show_window and self.window_available:
            try:
                cv2.imshow('TurtleBot 4 - YOLO Detection', annotated)
                cv2.waitKey(1)
            except cv2.error as exc:
                self.window_available = False
                self.get_logger().warning(f'OpenCV window disabled: {exc}')

    def destroy_node(self):
        """Close the OpenCV window before releasing ROS resources."""
        if self.show_window and self.window_available:
            cv2.destroyAllWindows()
        return super().destroy_node()


def main(args=None):
    """Start the YOLO detector node."""
    rclpy.init(args=args)
    node = None
    try:
        node = YoloDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        if node is not None:
            node.get_logger().fatal(str(exc))
        else:
            print(f'[yolo_detector] FATAL: {exc}')
        raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
