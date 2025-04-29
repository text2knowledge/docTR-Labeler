from unittest.mock import MagicMock

import pytest
from tkinter import CURRENT, Canvas, Tk

from labeler.components import Polygon
from labeler.views import ImageOnCanvas


@pytest.fixture
def gui_app():
    root = MagicMock(Tk)
    root.type_options = ["option1", "option2", "option3"]
    root.label_variable = MagicMock()
    root.type_variable = MagicMock()
    root.show_case_type_variable = MagicMock()
    root.img_cnv = MagicMock(ImageOnCanvas)
    root.img_cnv.polygons = [MagicMock(Polygon)]
    canvas = MagicMock(Canvas)
    return root, canvas


def test_get_pt_center(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)
    canvas.coords = MagicMock(return_value=[10, 10, 10, 10])

    point_id = poly.points[0]
    center = poly.get_pt_center(point_id)
    assert center == (10, 10)


def test_leave_poly(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)
    root.label_variable = MagicMock()
    root.show_case_type_variable = MagicMock()

    poly.leave_poly()

    canvas.itemconfigure.assert_called_with(CURRENT, stipple="", fill="")
    root.label_variable.set.assert_called_with("")
    root.show_case_type_variable.set.assert_called_with(root.type_options[0])


def test_draw_points(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    poly.update_point = MagicMock()
    poly.draw_points()

    # Check if the update_point was called for each point
    assert poly.update_point.call_count == len(pts)


def test_enter_poly(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    root.label_variable = MagicMock()
    root.show_case_type_variable = MagicMock()

    poly.enter_poly()

    # Verify that the polygon's color changed and that the label and type were set
    canvas.itemconfigure.assert_called_with(CURRENT, stipple="gray25", fill="blue")
    root.label_variable.set.assert_called_with(poly.text)
    root.show_case_type_variable.set.assert_called_with(poly.poly_type)


def test_chkup(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    # Simulate the event for mouse release
    event = MagicMock()
    event.widget.unbind = MagicMock()

    # Simulate the chkup event
    poly.chkup(event)

    # Verify that unbind and cursor reset are called
    event.widget.unbind.assert_called_with("<B1-Motion>")
    root.config.assert_called_with(cursor="")


def test_motion(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    canvas.coords = MagicMock()
    poly.update_polygon = MagicMock()
    poly.draw_points = MagicMock()

    # Simulate motion event
    event = MagicMock()
    event.x = 15
    event.y = 15

    # Simulate find_withtag returning a valid point ID
    mock_point_id = poly.points[0]
    canvas.find_withtag = MagicMock(return_value=[mock_point_id])

    # Mock the canvasx and canvasy methods to return the event's x and y
    mock_widget = MagicMock()
    mock_widget.canvasx = MagicMock(return_value=15)
    mock_widget.canvasy = MagicMock(return_value=15)
    poly.point_in_use = mock_widget
    poly.motion(event)

    canvas.coords.assert_called()
    poly.update_polygon.assert_called()
    poly.draw_points.assert_called()


def test_deselect_poly(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    poly.select_polygon()
    poly.deselect_poly()

    # Check if the polygon is deselected
    canvas.itemconfigure.assert_called_with(poly.polygon, fill="", stipple="")
    assert poly.select_poly is False
    assert poly.down_inside_poly is False
    assert poly.radius == 1  # Ensure points were resized back to smaller size


def test_polygon_initialization(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    assert poly.pt_coords == pts
    assert poly.points
    assert poly.polygon
    assert len(poly.points) == len(pts)


def test_polygon_update_point(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)
    canvas.coords = MagicMock()

    poly.update_point(poly.points[0], 15, 15)

    canvas.coords.assert_called_with(poly.points[0], 14, 14, 16, 16)


def test_polygon_select(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    poly.select_polygon()

    # Check if the polygon is selected (color changed)
    canvas.itemconfigure.assert_called_with(poly.polygon, fill="red", stipple="gray50")
    assert poly.select_poly is True


def test_polygon_deselect(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    poly.select_polygon()
    poly.deselect_poly()

    # Check if the polygon is deselected (color reset)
    canvas.itemconfigure.assert_called_with(poly.polygon, fill="", stipple="")
    assert poly.select_poly is False


def test_polygon_mouse_down_and_up(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    # Simulate mouse down event on a point
    event_down = MagicMock()
    poly.down(event_down)

    # Simulate mouse up event on a point
    event_up = MagicMock()
    poly.chkup(event_up)

    # Check if the point was bound correctly
    assert poly.point_in_use == event_down.widget
    event_up.widget.unbind.assert_called_with("<B1-Motion>")
    assert poly.root.config.call_count > 0  # Check if cursor was set to crosshair during motion


def test_polygon_delete(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)
    canvas.delete = MagicMock()

    poly.delete_self()

    canvas.delete.assert_any_call(poly.polygon)
    for point in poly.points:
        canvas.delete.assert_any_call(point)


def test_polygon_update_polygon(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20], [30, 30]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    canvas.coords = MagicMock()
    poly.update_polygon()
    canvas.coords.assert_called_with(poly.polygon, *poly._flatten())


def test_down_poly_sets_flags(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    event = MagicMock()
    poly.down_poly(event)

    assert poly.down_inside_poly is True
    assert root.polygon_in_use is True


def test_chkup_poly_toggle_selection(gui_app):
    root, canvas = gui_app
    root.type_options = ["Text", "Other"]
    pts = [[10, 10], [20, 20]]
    poly = Polygon(root=root, canvas=canvas, pts=pts, poly_type="Text")

    # Mock CURRENT and canvas methods
    canvas.itemconfigure = MagicMock()
    canvas.tag_raise = MagicMock()
    poly.points_bigger = MagicMock()
    poly.points_smaller = MagicMock()
    poly.draw_points = MagicMock()

    # First call: should select polygon
    poly.down_inside_poly = True
    poly.select_poly = False

    poly.chkup_poly()

    assert poly.select_poly is True
    canvas.itemconfigure.assert_called_with(CURRENT, fill="red", stipple="gray50")
    poly.points_bigger.assert_called_once()
    poly.points_smaller.assert_not_called()
    poly.draw_points.assert_not_called()
    assert poly.down_inside_poly is False

    # Second call: should deselect polygon
    poly.down_inside_poly = True
    poly.select_poly = True
    canvas.itemconfigure.reset_mock()
    poly.points_bigger.reset_mock()
    poly.points_smaller.reset_mock()
    poly.draw_points.reset_mock()

    poly.chkup_poly()

    assert poly.select_poly is False
    canvas.itemconfigure.assert_called_with(CURRENT, fill="", stipple="")
    poly.points_smaller.assert_called_once()
    poly.draw_points.assert_called_once()
    canvas.tag_raise.assert_called_with(poly.polygon)
    assert poly.down_inside_poly is False


def test_enter(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    event = MagicMock()
    poly.enter(event)

    assert poly.loc == 1


def test_update_color(gui_app):
    root, canvas = gui_app
    pts = [[10, 10], [20, 20]]
    poly = Polygon(root=root, canvas=canvas, pts=pts)

    event = MagicMock()
    poly.update_color(event)
