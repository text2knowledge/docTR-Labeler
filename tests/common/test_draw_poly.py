from unittest.mock import MagicMock

import pytest

from labeler.components import DrawPoly


@pytest.fixture
def drawpoly_fixture():
    root_mock = MagicMock()
    canvas_mock = MagicMock()
    img_on_cnv_mock = MagicMock()
    finish_func_mock = MagicMock()

    # Mock canvas methods
    canvas_mock.canvasx.return_value = 0
    canvas_mock.canvasy.return_value = 0
    canvas_mock.create_oval.return_value = MagicMock()  # Mock the oval drawing

    draw_poly = DrawPoly(root=root_mock, canvas=canvas_mock, img_on_cnv=img_on_cnv_mock, finish_func=finish_func_mock)

    return draw_poly, canvas_mock, img_on_cnv_mock, finish_func_mock


def test_initialization(drawpoly_fixture):
    draw_poly, canvas_mock, _, _ = drawpoly_fixture
    assert isinstance(draw_poly, DrawPoly)
    assert draw_poly.canvas == canvas_mock
    assert draw_poly.points == []
    assert draw_poly.pt_coords == []
    assert draw_poly.polygon is None
    assert draw_poly.radius == 1


def test_draw_point_when_not_drawing_polygon(drawpoly_fixture):
    draw_poly, _, img_on_cnv_mock, finish_func_mock = drawpoly_fixture
    # Mock values for x and y
    event_mock = MagicMock()
    event_mock.x = 10
    event_mock.y = 10
    img_on_cnv_mock.drawing_polygon = False  # Simulate not drawing a polygon
    img_on_cnv_mock.img_width = 100
    img_on_cnv_mock.img_height = 100
    img_on_cnv_mock.scale_factor = 1

    draw_poly.draw_point(event_mock)

    assert len(draw_poly.points) == 0
    assert finish_func_mock.call_count == 0


def test_draw_point_within_bounds(drawpoly_fixture):
    draw_poly, _, img_on_cnv_mock, finish_func_mock = drawpoly_fixture
    # Mock values for x and y
    event_mock = MagicMock()
    event_mock.x = 10
    event_mock.y = 10
    img_on_cnv_mock.drawing_polygon = True
    img_on_cnv_mock.img_width = 100
    img_on_cnv_mock.img_height = 100
    img_on_cnv_mock.scale_factor = 1

    draw_poly.draw_point(event_mock)

    assert len(draw_poly.points) == 1
    assert finish_func_mock.call_count == 0  # Since the polygon hasn't been completed yet

    # Reset points
    draw_poly.points = []
    # Call the draw_point method 4 times (to complete the polygon)
    for _ in range(4):
        draw_poly.draw_point(event_mock)

    assert len(draw_poly.points) == 4
    assert finish_func_mock.call_count == 1


def test_draw_point_out_of_bounds(drawpoly_fixture):
    draw_poly, _, img_on_cnv_mock, finish_func_mock = drawpoly_fixture
    # Mock values for x and y
    event_mock = MagicMock()
    event_mock.x = 200
    event_mock.y = 200
    img_on_cnv_mock.drawing_polygon = True
    img_on_cnv_mock.img_width = 100
    img_on_cnv_mock.img_height = 100
    img_on_cnv_mock.scale_factor = 1

    draw_poly.draw_point(event_mock)

    assert len(draw_poly.points) == 0
    finish_func_mock.assert_not_called()


def test_enter_point(drawpoly_fixture):
    draw_poly, canvas_mock, _, _ = drawpoly_fixture
    point_mock = MagicMock()
    canvas_mock.find_withtag.return_value = [point_mock]

    draw_poly.enter_point(None)

    canvas_mock.itemconfigure.assert_called_once_with(point_mock, fill="blue")


def test_leave_point(drawpoly_fixture):
    draw_poly, canvas_mock, _, _ = drawpoly_fixture
    point_mock = MagicMock()
    canvas_mock.find_withtag.return_value = [point_mock]

    draw_poly.leave_point(None)

    canvas_mock.itemconfigure.assert_called_once_with(point_mock, fill="green")


def test_chkup_rmb_point(drawpoly_fixture):
    draw_poly, canvas_mock, _, _ = drawpoly_fixture
    point_mock = MagicMock()
    canvas_mock.find_withtag.return_value = [point_mock]

    draw_poly.points.append(point_mock)
    draw_poly.pt_coords.append([10, 10])

    # Call the chkup_rmb_point method to remove the point
    draw_poly.chkup_rmb_point(None)

    # Verify that the point was removed from the canvas
    canvas_mock.delete.assert_called_once_with(point_mock)
    assert len(draw_poly.points) == 0
    assert len(draw_poly.pt_coords) == 0


def test_delete_self(drawpoly_fixture):
    draw_poly, canvas_mock, _, _ = drawpoly_fixture
    point_mock = MagicMock()
    draw_poly.points.append(point_mock)
    draw_poly.pt_coords.append([10, 10])

    canvas_mock.create_oval = MagicMock(return_value=point_mock)

    canvas_mock.delete = MagicMock()
    draw_poly.delete_self()

    # Verify that the points were deleted from the canvas
    canvas_mock.delete.assert_called_once_with(point_mock)

    # Ensure that the points are removed from the list
    assert len(draw_poly.pt_coords) == 0
    assert draw_poly.polygon is None
