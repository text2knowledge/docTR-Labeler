# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import os

import cv2
import numpy as np
from onnxtr.io import DocumentFile
from onnxtr.models import from_hub, ocr_predictor

__all__ = ["AutoLabeler"]


class AutoLabeler:
    """
    AutoLabeler class to predict text from an image and return the polygons and texts.
    """

    def __init__(self):
        self.predictor = ocr_predictor(
            det_arch=self._load_arch(os.environ.get("DETECTION_ARCH", "fast_base")),
            reco_arch=self._load_arch(os.environ.get("RECOGNITION_ARCH", "Felix92/onnxtr-parseq-multilingual-v1")),
            det_bs=1,
            reco_bs=256,
            assume_straight_pages=False,
            straighten_pages=False,
            export_as_straight_boxes=False,
            preserve_aspect_ratio=True,
            symmetric_pad=True,
            detect_orientation=False,
            detect_language=False,
            disable_crop_orientation=True,
            disable_page_orientation=True,
        )
        self.objectness_threshold = float(os.environ.get("OBJECTNESS_THRESHOLD", 0.5))

    def _load_arch(self, arch: str) -> str:
        # For HF hub models
        if arch.count("/") == 1:
            return from_hub(arch)
        # Otherwise OnnxTR downloaded models or local OnnxTR
        return arch

    def _to_absolute(self, geom: tuple[tuple[float, float]], img_shape: tuple[int, int]) -> list[list[int]]:
        """
        Convert relative coordinates to absolute coordinates.

        Args:
            geom: tuple[tuple[float, float]]: List of points in relative coordinates
            img_shape: tuple[int, int]: Shape of the image

        Returns:
            list[list[int]]: List of points in absolute coordinates
        """
        h, w = img_shape
        if len(geom) == 2:  # Assume straight pages = True -> [[xmin, ymin], [xmax, ymax]]
            (xmin, ymin), (xmax, ymax) = geom
            xmin, xmax = int(round(w * xmin)), int(round(w * xmax))
            ymin, ymax = int(round(h * ymin)), int(round(h * ymax))
            return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
        # Assume straight pages = False -> [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        else:  # For polygons, convert each point to absolute coordinates
            return [[int(point[0] * w), int(point[1] * h)] for point in geom]

    def predict(self, image_path: str) -> dict[str, list[list[list[int]]] | list[str]]:
        """
        Predict text from an image and return the polygons and texts.

        Args:
            image_path: str: Path to the image

        Returns:
            dict[str, list[list[list[int]]] | list[str]]: Dictionary containing the polygons and texts
        """
        polygons = []
        texts = []
        doc = DocumentFile.from_images(image_path)
        res = self.predictor(doc)
        json_res = res.export()
        for page in json_res["pages"]:
            shape = page["dimensions"]
            for block in page["blocks"]:
                for line in block["lines"]:
                    for word in line["words"]:
                        if word["objectness_score"] > self.objectness_threshold:
                            polygons.append(self._to_absolute(word["geometry"], shape))
                            texts.append(word["value"])

        return {"polygons": polygons, "texts": texts}

    def _extract_as_straight_box(self, image: np.ndarray, coords: list[list[int]]) -> np.ndarray:
        """
        Extract a 4-point polygon from the image and warp it into a straight rectangular crop.

        Args:
            image (np.ndarray): The input image.
            coords (list[list[int]]): List of 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].


        Returns:
            np.ndarray: The straightened rectangular crop.
        """
        src_points = np.array(coords, dtype="float32")

        # Determine the bounding box dimensions (width and height of the rectangle)
        width = max(  # type: ignore[call-overload]
            np.linalg.norm(src_points[0] - src_points[1]),
            np.linalg.norm(src_points[2] - src_points[3]),
        )
        height = max(  # type: ignore[call-overload]
            np.linalg.norm(src_points[0] - src_points[3]),
            np.linalg.norm(src_points[1] - src_points[2]),
        )

        # Define the destination points for the rectangle
        dst_points = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")

        # Compute the perspective transform matrix & warp the image
        transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        return cv2.warpPerspective(image, transform_matrix, (int(width), int(height)))

    def predict_label(self, image_path: str, coords: list[list[int]]) -> str:
        """
        Predict text from an image and return the text for the given coordinates.

        Args:
            image_path: str: Path to the image
            coords: list[list[int]]: List of 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

        Returns:
            str: The predicted text
        """
        doc = DocumentFile.from_images(image_path)
        try:
            crop = self._extract_as_straight_box(doc[0], coords)
        except Exception:  # pragma: no cover
            # Return empty string if the crop is not valid
            return ""
        res = self.predictor.reco_predictor([crop])
        return res[0][0].strip()
