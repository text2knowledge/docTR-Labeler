# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import numpy as np
from onnxtr.io import DocumentFile
from onnxtr.models import from_hub, ocr_predictor
from onnxtr.utils import extract_rcrops

__all__ = ["AutoLabeler"]


class AutoLabeler:
    """
    AutoLabeler class to predict text from an image and return the polygons and texts.
    """

    def __init__(self):
        self.predictor = ocr_predictor(
            det_arch="fast_base",
            reco_arch=from_hub("Felix92/onnxtr-parseq-multilingual-v1"),
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
                        if word["objectness_score"] > 0.8:
                            polygons.append(self._to_absolute(word["geometry"], shape))
                            texts.append(word["value"])

        return {"polygons": polygons, "texts": texts}

    def predict_label(self, image_path: str, coords: list[list[int]]) -> str:
        doc = DocumentFile.from_images(image_path)
        # convert coords to numpy array and add batch dimension
        np_coords = np.array([coords])
        crop = extract_rcrops(doc[0], np_coords)
        res = self.predictor.reco_predictor(crop)
        return res[0][0].strip()
