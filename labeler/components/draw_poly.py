# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from collections.abc import Callable
from typing import Any

from tkinter import Event

from ..logger import logger

__all__ = ["DrawPoly"]


class DrawPoly:
    """
    Class to draw a polygon on the canvas

    Args:
        root: Any: The root tkinter object
        canvas: Any: The canvas object on which the image is drawn
        img_on_cnv: Any: The image on the canvas
        finish_func: Callable: The function to call when the polygon is finished
    """

    def __init__(self, root: Any, canvas: Any, img_on_cnv: Any, finish_func: Callable):
        self.root = root
        self.canvas = canvas
        self.img_on_cnv = img_on_cnv
        self.points = []  # type: ignore[var-annotated]
        self.pt_coords = []  # type: ignore[var-annotated]
        self.polygon = None
        self.radius = 1
        self.canvas.update()
        self.x1, self.y1 = canvas.canvasx(0), canvas.canvasy(0)
        self.canvas.bind("<ButtonRelease-1>", self.draw_point)
        self.finish = finish_func

    def draw_point(self, event):
        if self.img_on_cnv.drawing_polygon is False:
            logger.info("Point not drawn because not drawing polygon")
            return
        else:
            x, y = event.x + self.x1, event.y + self.y1
            if (
                x > self.img_on_cnv.img_width * self.img_on_cnv.scale_factor
                or y > self.img_on_cnv.img_height * self.img_on_cnv.scale_factor
            ):
                logger.info("Point not drawn because out of bounds")
                return
            else:
                self.pt_coords.append([x, y])
                self.points.append(
                    self.canvas.create_oval(
                        x - self.radius, y - self.radius, x + self.radius, y + self.radius, fill="green", tag="Point"
                    )
                )
                self.canvas.tag_bind(self.points[-1], "<Enter>", self.enter_point)
                self.canvas.tag_bind(self.points[-1], "<Leave>", self.leave_point)
                self.canvas.tag_bind(self.points[-1], "<ButtonRelease-3>", self.chkup_rmb_point)
                if len(self.points) == 4:
                    logger.info("Polygon drawn")
                    self.finish()

    def enter_point(self, event: Event | None = None):
        """
        Change the color of the point when the cursor enters it

        Args:
            event: Event: The tkinter event
        """
        pt = self.canvas.find_withtag("current")[0]
        self.canvas.itemconfigure(pt, fill="blue")

    def leave_point(self, event: Event | None = None):
        """
        Change the color of the point when the cursor leaves it

        Args:
            event: Event: The tkinter event
        """
        pt = self.canvas.find_withtag("current")[0]
        self.canvas.itemconfigure(pt, fill="green")

    def chkup_rmb_point(self, event: Event | None = None):
        """
        Check if the right mouse button is pressed on a point

        Args:
            event: Event: The tkinter event
        """
        pt = self.canvas.find_withtag("current")[0]
        index_pt = self.points.index(pt)
        self.canvas.delete(pt)
        self.points.pop(index_pt)
        self.pt_coords.pop(index_pt)

    def delete_self(self):
        """
        Delete the polygon and points from the canvas
        """
        for pt in self.points:
            self.canvas.delete(pt)
        self.pt_coords = []
        self.polygon = None
        self.canvas.update()
