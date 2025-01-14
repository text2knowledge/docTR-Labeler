# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import uuid
from typing import Any

from tkinter import CURRENT, Event

__all__ = ["Polygon"]


class Polygon:
    """
    Polygon class to handle polygon drawing and manipulation

    Args:
        root: Any: The root tkinter object
        canvas: Any: The canvas object on which the image is drawn
        pts: list: List of lists containing the coordinates of the points of the polygon
    """

    def __init__(self, root: Any, canvas: Any, pts: list[list[int]], poly_type: str | None = None, text: str = ""):
        self.canvas = canvas
        self.root = root
        self.points: Any = []
        self.enter_status = [0] * len(pts)
        self.drag_status = [0] * len(pts)
        self.pt_coords = pts
        self.original_coords = pts
        self.point_in_use = None
        self.poly_type = poly_type or self.root.type_options[0]
        self.text = text
        self.radius = 1
        self.scale_factor = 1.0
        self.inside_poly = False
        self.down_inside_poly = False
        self.select_poly = False
        self.colors = ["#FF0000", "#FFFF00", "#00FF00", "#0000FF", "#800000", "#00FFFF", "#FFFFFF", "#800080"]
        self.polygon_id = str(uuid.uuid4())
        # Add points to list of points
        self.initialize_points()
        # Create a polygon tkinter widget
        self.polygon = self.canvas.create_polygon(self._flatten(), outline="red", fill="", tag="Quad")
        self.draw_points()
        for pt in self.points:
            # Binds point on which LMB(Left Mouse Button is pressed)
            self.canvas.tag_bind(pt, "<ButtonPress-1>", self.down)
            # Binds point on which LMB is unpressed
            self.canvas.tag_bind(pt, "<ButtonRelease-1>", self.chkup)
            # Binds self.enter to point on which the cursor enters
            self.canvas.tag_bind(pt, "<Enter>", self.enter)
            # Binds self.leave to point on which the cursor exits
            self.canvas.tag_bind(pt, "<Leave>", self.leave)

        self.canvas.tag_bind(self.polygon, "<Enter>", self.enter_poly)
        self.canvas.tag_bind(self.polygon, "<Leave>", self.leave_poly)
        self.canvas.tag_bind(self.polygon, "<ButtonPress-1>", self.down_poly)
        self.canvas.tag_bind(self.polygon, "<ButtonRelease-1>", self.chkup_poly)

    def enter_poly(self, event: Event | None = None):
        """
        Change the color of the polygon when the cursor enters it

        Args:
            event: Event: The event object
        """
        self.inside_poly = True
        if self.select_poly is False:
            self.canvas.itemconfigure(CURRENT, stipple="gray25", fill="blue")

        # Set the label and type if a polygon is selected
        any_selected = any(hasattr(poly, "select_poly") and poly.select_poly for poly in self.root.img_cnv.polygons)
        if not any_selected:
            self.root.label_variable.set(self.text)
            self.root.type_variable.set(self.poly_type)

    def delete_self(self):
        """
        Delete the polygon and its points
        """
        for pt in self.points:
            self.canvas.delete(pt)
        self.canvas.delete(self.polygon)

    def leave_poly(self, event: Event | None = None):
        """
        Change the color of the polygon when the cursor leaves it

        Args:
            event: Event: The event object
        """
        self.inside_poly = False
        self.down_inside_poly = False
        if self.select_poly is False:
            self.canvas.itemconfigure(CURRENT, stipple="", fill="")
        # Reset the label and type if no polygon is selected
        if not any(hasattr(poly, "select_poly") and poly.select_poly for poly in self.root.img_cnv.polygons):
            self.root.label_variable.set("")
            self.root.type_variable.set(self.root.type_options[0])

    def down_poly(self, event: Event | None = None):
        """
        Check if the left mouse button is pressed on the polygon

        Args:
            event: Event: The event object
        """
        self.down_inside_poly = True
        self.root.polygon_in_use = True
        self.root.last_selected_polygon = self.polygon_id
        self.root.label_variable.set(self.text)
        self.root.type_variable.set(self.poly_type)

    def chkup_poly(self, event: Event | None = None):
        """
        Check if the left mouse button is unpressed on the polygon

        Args:
            event: Event: The event object
        """
        if self.down_inside_poly is True:
            if self.select_poly is False:
                self.canvas.itemconfigure(CURRENT, fill="red", stipple="gray50")
                self.select_poly = True
                self.points_bigger()
            elif self.select_poly is True:
                self.canvas.itemconfigure(CURRENT, fill="", stipple="")
                self.select_poly = False
                self.points_smaller()
                self.canvas.tag_raise(self.polygon)
                self.draw_points()
        self.down_inside_poly = False

    def _flatten(self):
        return [item for sublist in self.pt_coords for item in sublist]

    def initialize_points(self):
        """
        Initialize the points on the canvas - draw circular point widgets
        """
        for i in range(len(self.pt_coords)):
            if i < len(self.colors):
                fill_color = self.colors[i]
            else:
                fill_color = "green"
            self.points.append(
                self.canvas.create_oval(
                    self.pt_coords[i][0] - self.radius,
                    self.pt_coords[i][1] - self.radius,
                    self.pt_coords[i][0] + self.radius,
                    self.pt_coords[i][1] + self.radius,
                    activefill=fill_color,
                    fill=fill_color,
                    disabledfill="blue",
                    tag="Point",
                )
            )

    def enter(self, event: Event | None = None):
        """
        Triggered when the cursor enters the bound widget(A point in our case)
        """
        self.loc = 1

    def leave(self, event: Event | None = None):
        """
        Triggered when the cursor leaves the bound widget(A point in our case)
        """
        pass

    def draw_points(self, update_original: bool = False):
        """
        Draw the points on the canvas by updating their coordinates and then raising them on the canvas

        Args:
            update_original: bool: Whether to update the original coordinates of the points (default: False)
        """
        for i in range(len(self.points)):
            self.update_point(
                self.points[i], self.pt_coords[i][0], self.pt_coords[i][1], update_original=update_original
            )
        for pt in self.points:
            self.canvas.tag_raise(pt)

    def update_point(self, point_id: str | int, x: int, y: int, update_original: bool = False):
        """
        Update the coordinates of a point on the canvas

        Args:
            point_id: str | int: The id of the point to update
            x: int: The x-coordinate of the point
            y: int: The y-coordinate of the point
            update_original: bool: Whether to update the original coordinates of the point
        """
        self.canvas.coords(point_id, x - self.radius, y - self.radius, x + self.radius, y + self.radius)
        self.pt_coords[self.points.index(point_id)] = [x, y]
        if update_original:
            self.original_coords[self.points.index(point_id)] = [int(x / self.scale_factor), int(y / self.scale_factor)]

    def get_pt_center(self, point_id: str | int):
        """
        Get the center of a point on the canvas

        Args:
            point_id: str | int: The id of the point

        Returns:
            tuple: The center of the point
        """
        p = self.canvas.coords(point_id)
        return (int((p[0] + p[2]) / 2), int((p[1] + p[3]) / 2))

    def update_polygon(self):
        """
        Update the polygon according to the changed point in the polygon
        """
        self.canvas.coords(self.polygon, *self._flatten())
        self.pt_coords = [[int(x), int(y)] for x, y in self.pt_coords]
        self.original_coords = [[int(x), int(y)] for x, y in self.original_coords]

    def down(self, event: Event):
        """
        Triggered by a mouse click on a point
        """
        self.point_in_use = event.widget
        event.widget.bind("<B1-Motion>", self.motion)

    def motion(self, event: Event):
        """
        Triggered when a point is pressed and moved

        Args:
            event: Event: The event object
        """
        self.root.config(cursor="crosshair")
        self.point_in_use = event.widget
        pt = self.canvas.find_withtag("current")[0]
        self.update_point(
            pt,
            self.point_in_use.canvasx(event.x),  # type: ignore[attr-defined]
            self.point_in_use.canvasy(event.y),  # type: ignore[attr-defined]
            update_original=True,
        )
        self.update_polygon()
        self.draw_points()

    def chkup(self, event: Event):
        """
        Triggered when a point is unpressed
        """
        event.widget.unbind("<B1-Motion>")
        self.root.config(cursor="")

    def deselect_poly(self):
        """
        Deselect the current polygon
        """
        if self.select_poly is False:
            pass
        else:
            self.canvas.itemconfigure(self.polygon, fill="", stipple="")
            self.select_poly = False
            self.down_inside_poly = False
            self.points_smaller()

    def select_polygon(self):
        """
        Select the current polygon
        """
        if self.select_poly is True:
            pass
        else:
            self.canvas.itemconfigure(self.polygon, fill="red", stipple="gray50")
            self.select_poly = True
            self.points_bigger()

    def points_smaller(self):
        """
        Decrease the size of the drawn polygon edge points
        """
        self.radius = 1
        self.draw_points()

    def points_bigger(self):
        """
        Increase the size of the drawn polygon edge points
        """
        self.radius = 5
        self.draw_points()
