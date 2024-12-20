# Copyright (C) 2024-2024, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

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

    def tight_box(self):
        """
        Tighten the bounding box of the selected polygon by:
        1. Creating a mask of the polygon
        2. Finding the min-area rotated rectangle of the polygon
        3. Expanding the rotated rectangle by 2 pixels on each side
        4. Updating the polygon points to match the expanded rotated rectangle
        """
        for p in self.cnv.current_state()[0]:
            if p.select_poly:
                cnt = []
                for pt in p.points:
                    cnt.append(p.get_pt_center(pt))
                self.changed_poly.append([p, cnt])
                cnts = np.array(cnt).reshape((-1, 1, 2)).astype(np.int32)

                # Load and preprocess the image
                img = cv2.imread(self.cnv.image_path)
                img = cv2.resize(img, self.cnv.img.size, interpolation=cv2.INTER_AREA)
                mask = np.zeros(img.shape[:2], np.uint8)
                cv2.fillPoly(mask, pts=[cnts], color=(255, 255, 255))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, img = cv2.threshold(img, int(self.thresh), 255, cv2.THRESH_BINARY)
                new_img = cv2.bitwise_and(img, img, mask=mask)

                # Find new contours in the masked image
                new_cnts, _ = cv2.findContours(new_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                new_cnts = sorted(new_cnts, key=cv2.contourArea, reverse=True)[1:]
                all_pts = [pt for ct in new_cnts for pt in ct]

                # Find the min-area rotated rectangle
                min_area_rect = cv2.minAreaRect(np.array(all_pts).reshape((-1, 1, 2)).astype(np.int32))
                box = cv2.boxPoints(min_area_rect)
                box = np.intp(box)  # type: ignore[assignment]

                # Get the center, width, height, and angle from the min-area rectangle
                center, size, angle = min_area_rect
                w, h = size
                # If the width or height is less than 10, skip the polygon to avoid deletion
                if w < 10 or h < 10:
                    continue

                # Expand by 2 pixels on each side (increase width and height)
                size = (w + 2, h + 2)

                # Use the expanded size to create the new rotated rectangle
                expanded_rect = cv2.boxPoints(((center[0], center[1]), size, angle))
                expanded_rect = np.intp(expanded_rect)  # type: ignore[assignment]

                # Update polygon points to match the expanded rotated rectangle
                for i, point in enumerate(p.points):
                    p.update_point(point, expanded_rect[i][0], expanded_rect[i][1])

                p.update_polygon()
                p.draw_points()

    def discard_tight_box(self):
        """
        Discard the changes made to the polygons by the tight_box method
        """
        for p, pts in self.changed_poly:
            for i, pt in enumerate(p.points):
                p.update_point(pt, pts[i][0], pts[i][1])
            p.update_polygon()
            p.draw_points()
            p.pt_coords = pts
        self.cnv.canvas.update()
