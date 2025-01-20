# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from threading import Lock
from typing import Any

import cv2
import numpy as np

__all__ = ["TightBox"]


class TightBox:
    """
    Class to handle polygon tightening

    Args:
        root: Any: The root tkinter object
        cnv: Any: The canvas object on which the image is drawn
        thresh: float: The threshold value for the image
    """

    def __init__(self, root: Any, cnv: Any, thresh: float):
        self.root = root
        self.cnv = cnv
        self.thresh = thresh
        self.changed_poly: list[list[Any]] = []
        self.polygons_mutex = Lock()

    def tight_box(self):
        """
        Tighten the bounding box of the selected polygon by:
        1. Creating a mask of the polygon
        2. Finding the min-area rotated rectangle of the polygon
        3. Expanding the rotated rectangle by 2 pixels on each side
        4. Updating the polygon points to match the expanded rotated rectangle
        """
        with self.polygons_mutex:
            for p in self.cnv.current_state()[0]:
                if p.select_poly:
                    # Save original points for revert functionality
                    original_pts = [
                        [pt[0] / self.cnv.scale_factor, pt[1] / self.cnv.scale_factor] for pt in p.pt_coords
                    ]
                    self.changed_poly.append([p, original_pts])

                    cnts = np.array(original_pts).reshape((-1, 1, 2)).astype(np.int32)
                    img = cv2.imread(self.cnv.image_path)
                    img = cv2.resize(img, self.cnv.img.size, interpolation=cv2.INTER_AREA)
                    mask = np.zeros(img.shape[:2], np.uint8)
                    cv2.fillPoly(mask, pts=[cnts], color=(255, 255, 255))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, img = cv2.threshold(img, int(self.thresh), 255, cv2.THRESH_BINARY)
                    new_img = cv2.bitwise_and(img, img, mask=mask)

                    new_cnts, _ = cv2.findContours(new_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    new_cnts = sorted(new_cnts, key=cv2.contourArea, reverse=True)[1:]
                    all_pts = [pt for ct in new_cnts for pt in ct]

                    min_area_rect = cv2.minAreaRect(np.array(all_pts).reshape((-1, 1, 2)).astype(np.int32))
                    center, size, angle = min_area_rect
                    w, h = size

                    if w < 2 or h < 2:
                        continue  # Skip polygons with too small areas

                    # Expand by 2 pixels
                    size = (w + 2, h + 2)
                    expanded_rect = cv2.boxPoints(((center[0], center[1]), size, angle))
                    expanded_rect = np.intp(expanded_rect)  # type: ignore[assignment]

                    # Update points to match the expanded rotated rectangle
                    for i, point in enumerate(p.points):
                        new_x = expanded_rect[i][0] * self.cnv.scale_factor
                        new_y = expanded_rect[i][1] * self.cnv.scale_factor
                        p.update_point(point, new_x, new_y)

                    # Update original coordinates scaled to the original image size
                    p.original_coords = [
                        [int(x / self.cnv.scale_factor), int(y / self.cnv.scale_factor)] for x, y in p.pt_coords
                    ]
                    p.update_polygon()
                    p.draw_points()

    def discard_tight_box(self):
        """
        Discard changes made by the `tight_box` method.
        """
        with self.polygons_mutex:
            for p, original_pts in self.changed_poly:
                for i, pt in enumerate(p.points):
                    original_x = original_pts[i][0] * self.cnv.scale_factor
                    original_y = original_pts[i][1] * self.cnv.scale_factor
                    p.update_point(pt, original_x, original_y)

                p.update_polygon()
                p.draw_points()
            self.changed_poly = []  # Clear the history of changes
            self.cnv.canvas.update()
