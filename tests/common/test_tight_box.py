from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from labeler.automation import TightBox


@pytest.fixture
def mock_polygon():
    polygon = Mock()
    polygon.select_poly = True
    # Mocking pt_coords with tuples to allow arithmetic operations
    polygon.pt_coords = [(10, 20), (20, 20), (20, 10), (10, 10)]
    polygon.points = [Mock() for _ in range(4)]
    polygon.get_pt_center = Mock(side_effect=lambda pt: (10, 20))
    polygon.update_point = Mock()
    polygon.update_polygon = Mock()
    polygon.draw_points = Mock()
    return polygon


@pytest.fixture
def mock_canvas(mock_polygon):
    canvas = Mock()
    canvas.current_state = Mock(return_value=([mock_polygon],))
    canvas.image_path = "path/to/image.jpg"
    canvas.img.size = (100, 100)
    canvas.scale_factor = 1  # Setting a mock scale_factor value
    canvas.canvas.update = Mock()
    return canvas


@pytest.fixture
def tight_box(mock_canvas):
    root = Mock()
    thresh = 127
    return TightBox(root=root, cnv=mock_canvas, thresh=thresh)


def test_tight_box_with_valid_polygon(tight_box, mock_polygon):
    dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.imread = Mock(return_value=dummy_image)

    cv2.resize = Mock(return_value=dummy_image)
    cv2.cvtColor = Mock(return_value=dummy_image[:, :, 0])
    cv2.threshold = Mock(return_value=(None, dummy_image[:, :, 0]))
    cv2.bitwise_and = Mock(return_value=dummy_image[:, :, 0])
    cv2.findContours = Mock(
        return_value=([np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]], dtype=np.int32)], None)
    )
    cv2.minAreaRect = Mock(return_value=((15, 15), (10, 10), 0))
    cv2.boxPoints = Mock(return_value=np.array([[10, 10], [20, 10], [20, 20], [10, 20]]).astype(np.int32))

    tight_box.tight_box()

    assert mock_polygon.update_point.call_count == 4
    assert mock_polygon.update_polygon.called
    assert mock_polygon.draw_points.called


def test_tight_box_skips_small_polygons(tight_box, mock_polygon):
    dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.imread = Mock(return_value=dummy_image)
    cv2.resize = Mock(return_value=dummy_image)
    cv2.cvtColor = Mock(return_value=dummy_image[:, :, 0])
    cv2.threshold = Mock(return_value=(None, dummy_image[:, :, 0]))
    cv2.bitwise_and = Mock(return_value=dummy_image[:, :, 0])
    cv2.findContours = Mock(
        return_value=([np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]], dtype=np.int32)], None)
    )
    # Mock for a small polygon, below the threshold
    cv2.minAreaRect = Mock(return_value=((15, 15), (4, 4), 0))  # Width and height less than 5

    tight_box.tight_box()

    assert mock_polygon.update_point.call_count == 0
    assert not mock_polygon.update_polygon.called
    assert not mock_polygon.draw_points.called


def test_discard_tight_box(tight_box, mock_polygon, mock_canvas):
    tight_box.changed_poly = [(mock_polygon, [(10, 10), (20, 10), (20, 20), (10, 20)])]

    tight_box.discard_tight_box()

    assert mock_polygon.update_point.call_count == 4
    assert mock_polygon.update_polygon.called
    assert mock_polygon.draw_points.called
    assert mock_canvas.canvas.update.called
