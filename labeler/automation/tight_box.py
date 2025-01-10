# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from typing import Any

import cv2
import numpy as np

from ..logger import logger

__all__ = ["TightBox"]


class TightBox:
    """
    Class to handle polygon tightening with support for zoom adjustments.

    Args:
        root: Any: The root tkinter object
        cnv: Any: The canvas object on which the image is drawn
        thresh: float: The threshold value for the image
        expansion: int: Number of pixels to expand the bounding box
    """

    def __init__(self, root: Any, cnv: Any, thresh: float, expansion: int = 2):
        self.root = root
        self.cnv = cnv
        self.thresh = thresh
        self.expansion = expansion  # Adjustable expansion size
        self.changed_poly: list[list[Any]] = []

    def tight_box(self):
        """
        Tighten the bounding box of the selected polygon by:
        1. Creating a mask of the polygon
        2. Finding the min-area rotated rectangle of the polygon
        3. Expanding the rotated rectangle by 2 pixels on each side
        4. Updating the polygon points to match the expanded rotated rectangle
        """
        zoom = self.cnv.scale_factor  # Retrieve current zoom factor

        for p in self.cnv.current_state()[0]:
            if not p.select_poly:
                continue

            try:
                # Adjust points based on zoom factor
                cnt = [p.get_pt_center(pt) for pt in p.points]
                cnt = [(int(x / zoom), int(y / zoom)) for x, y in cnt]  # Unzoom coordinates

                self.changed_poly.append([p, cnt])
                cnts = np.array(cnt).reshape((-1, 1, 2)).astype(np.int32)

                img = cv2.imread(self.cnv.image_path)
                img = cv2.resize(img, self.cnv.img.size, interpolation=cv2.INTER_AREA)
                mask = np.zeros(img.shape[:2], np.uint8)
                cv2.fillPoly(mask, pts=[cnts], color=(255, 255, 255))
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, img_thresh = cv2.threshold(img_gray, int(self.thresh), 255, cv2.THRESH_BINARY)
                masked_img = cv2.bitwise_and(img_thresh, img_thresh, mask=mask)

                new_cnts, _ = cv2.findContours(masked_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                # Skip if no contours are found
                if len(new_cnts) < 2:
                    continue

                all_pts = [pt for ct in new_cnts[1:] for pt in ct]

                min_area_rect = cv2.minAreaRect(np.array(all_pts).reshape((-1, 1, 2)).astype(np.int32))
                center, size, angle = min_area_rect
                w, h = size
                # Skip if width or height is less than 5 pixels
                if w < 5 or h < 5:
                    continue

                # Expand and adjust rectangle
                expanded_rect = cv2.boxPoints(((center[0], center[1]), (w + self.expansion, h + self.expansion), angle))
                expanded_rect = np.intp(expanded_rect)
                expanded_rect_zoomed = [(x * zoom, y * zoom) for x, y in expanded_rect]

                # Update polygon points
                self._update_polygon_points(p, expanded_rect_zoomed)

            except Exception as e:
                logger.error(f"Error tightening polygon: {e}")

    def discard_tight_box(self):
        for p, pts in self.changed_poly:
            original_pts = [(x * self.cnv.scale_factor, y * self.cnv.scale_factor) for x, y in pts]
            self._update_polygon_points(p, original_pts, reset=True)
        self.cnv.canvas.update()

    def _update_polygon_points(self, polygon, points, reset=False):
        for i, point in enumerate(points):
            polygon.update_point(polygon.points[i], point[0], point[1])
        polygon.update_polygon()
        polygon.draw_points()
        if reset:
            polygon.pt_coords = points  # Ensure original points are restored correctly
