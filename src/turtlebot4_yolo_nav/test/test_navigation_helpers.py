import math

import pytest

from turtlebot4_yolo_nav.navigate_goals import yaw_to_quaternion


@pytest.mark.parametrize(
    'yaw, expected_z, expected_w',
    [
        (0.0, 0.0, 1.0),
        (math.pi / 2.0, math.sqrt(0.5), math.sqrt(0.5)),
        (math.pi, 1.0, 0.0),
    ],
)
def test_yaw_to_quaternion(yaw, expected_z, expected_w):
    z, w = yaw_to_quaternion(yaw)
    assert z == pytest.approx(expected_z)
    assert w == pytest.approx(expected_w, abs=1e-12)

