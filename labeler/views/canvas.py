# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import hashlib
import json
import os
from threading import Lock
from typing import Any

from PIL import Image, ImageTk
from tkinter import Event

from ..automation import auto_annotator
from ..components import Polygon
from ..logger import logger


class ImageOnCanvas:
    """
    Class to handle the image on the canvas

    Args:
        root: Any: The root tkinter object
        canvas: Any: The canvas object on which the image is drawn
        image_path: str: The path to the image file
    """

    def __init__(self, root: Any, canvas: Any, image_path: str):
        self.image_path = image_path
        self.root_path = os.path.split(os.path.split(self.image_path)[0])[0]
        self.tmp_labels_path = os.path.join(self.root_path, "tmp_annotations")
        self.root = root
        self.canvas = canvas

        self.img = Image.open(self.image_path)
        self.img_width, self.img_height = self.img.size

        self.canvas.update()
        self.imagetk = ImageTk.PhotoImage(self.img)
        self.scale_factor = round(self.img.size[0] / self.img_width, 1)

        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.imagetk)
        canvas.config(scrollregion=canvas.bbox("all"))
        self.canvas.update()
        self.polygons: list[Polygon] = []
        self.polygons_mutex = Lock()
        self.load_json()
        self.drawing_polygon = False
        self.current_saved = True

        # Bind zoom events
        self.root.bind("<Control-Key-plus>", self.zoom)
        self.root.bind("<Control-Key-minus>", self.zoom)
        self.root.bind("<Control-Key-equal>", self.zoom)  # For keyboards where '+' is 'Shift + ='

    def zoom(self, event: Event | None = None):
        """Handle zooming in and out."""
        zoom_step = 0.1  # Zoom step size
        max_zoom = min(float(os.environ.get("DOCTR_LABELER_MAX_ZOOM", 1.5)), 2.0)  # Maximum zoom capped at 2.0
        min_zoom = max(float(os.environ.get("DOCTR_LABELER_MIN_ZOOM", 0.5)), 0.1)  # Minimum zoom capped at 0.1
        previous_scale_factor = self.scale_factor

        # Zoom in
        if event.keysym in ["plus", "equal", "KP_Add"]:  # type: ignore[union-attr]
            if self.scale_factor < max_zoom:
                self.scale_factor = round(self.scale_factor + zoom_step, 1)

        # Zoom out
        elif event.keysym in ["minus", "KP_Subtract"]:  # type: ignore[union-attr]
            if self.scale_factor > min_zoom:
                self.scale_factor = round(self.scale_factor - zoom_step, 1)

        if self.scale_factor != previous_scale_factor:
            self.apply_zoom()

    def apply_zoom(self):
        """Apply the zoom scaling to all canvas elements and resize the image."""
        # Resize the image
        new_width = int(self.img_width * self.scale_factor)
        new_height = int(self.img_height * self.scale_factor)
        resized_img = self.img.resize((new_width, new_height))
        self.imagetk = ImageTk.PhotoImage(resized_img)

        # Update the canvas image
        self.canvas.itemconfig(self.canvas_img, image=self.imagetk)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        with self.polygons_mutex:
            for polygon in self.polygons:
                polygon.scale_factor = self.scale_factor
                # Calculate new coordinates based on original ones
                polygon.pt_coords = [
                    [int(x * self.scale_factor), int(y * self.scale_factor)]
                    for x, y in polygon.original_coords  # Use original unscaled coordinates
                ]
                polygon.update_polygon()
                polygon.draw_points()

        logger.info(f"Zoom applied: scale_factor={self.scale_factor}")

    def current_state(self) -> tuple[list[Polygon], bool]:
        """
        Get the current state of the polygons

        Returns:
            tuple[list[Polygon], bool]: The list of polygons, drawing status
        """
        return self.polygons, self.drawing_polygon

    def auto_annotate(self):
        """
        Auto annotate the image
        """
        logger.info(f"Auto annotating image: {self.image_path}")
        pre_annotations = auto_annotator.predict(self.image_path)
        poly_coords = pre_annotations["polygons"]
        poly_texts = pre_annotations["texts"]
        poly_types = [self.root.type_options[0]] * len(poly_coords)
        self.draw_polys(poly_coords, poly_types, poly_texts)  # type: ignore[arg-type]

    def auto_label(self, polygon: Polygon):
        """
        Auto label the image crop

        Args:
            polygon: Polygon: The polygon to label
        """
        coords = polygon.original_coords
        pre_label = auto_annotator.predict_label(self.image_path, coords)
        polygon.text = pre_label

    def _get_img_hash(self):
        """
        Compute the SHA256 hash of the image
        """
        with open(self.image_path, "rb") as fl:
            return hashlib.sha256(fl.read()).hexdigest()

    def load_json(self):
        """
        Load the annotation data for the current image.

        The method first tries to load annotations from the temporary annotations folder,
        and if not available, falls back to the pre_annotations.json file.
        """
        self.drawing_polygon = True
        self.pre_annotations_json_path = os.path.join(self.root_path, "pre_annotations.json")
        self.tmp_annotations_folder = os.path.join(self.root_path, "tmp_annotations")
        pre_annotations = {}
        temp_annotations = {}

        # Load annotations from the temp folder
        if os.path.exists(self.tmp_annotations_folder):
            img_name = os.path.split(self.image_path)[-1]
            img_base_name = os.path.splitext(img_name)[0]
            temp_annotation_file = os.path.join(self.tmp_annotations_folder, f"{img_base_name}.json")
            logger.info(f"Looking for temporary annotations in {temp_annotation_file}")

            if os.path.exists(temp_annotation_file):
                try:
                    with open(temp_annotation_file, "r", encoding="utf-8") as temp_file:
                        temp_annotations = json.load(temp_file)
                    logger.info(f"Loaded temporary annotations for {img_name}")
                except Exception as e:
                    logger.warning(f"Error loading temporary annotations for {img_name}: {e}")

        # If no temp annotations found, load from pre_annotations.json
        if not temp_annotations and os.path.exists(self.pre_annotations_json_path):
            try:
                with open(self.pre_annotations_json_path, "r", encoding="utf-8") as pre_file:
                    pre_annotations = json.load(pre_file)
                logger.info(f"Loaded pre-annotations from {self.pre_annotations_json_path}")
            except Exception as e:
                logger.warning(f"Error loading pre-annotations: {e}")

        # Get the image name for which annotations are required
        img_name = os.path.split(self.image_path)[-1]

        # Load the annotations from temp_annotations if available, otherwise from pre_annotations
        annotations = temp_annotations.get(img_name, {}) if temp_annotations else pre_annotations.get(img_name, {})

        # If annotations are found, process them
        if annotations:
            polygons = annotations.get("polygons", [])
            labels = annotations.get("labels", ["" for _ in polygons])
            types = annotations.get("types", [self.root.type_options[0]] * len(polygons))

            self.draw_polys(polygons, types, labels)

            logger.info(f"Loaded {len(polygons)} polygons from annotations")
        self.drawing_polygon = False

    def save_json(self) -> str:
        """
        Save the current state of the polygons to a json file

        Returns:
            str: The path to the saved json file
        """
        if not os.path.exists(self.tmp_labels_path):
            os.makedirs(self.tmp_labels_path)

        polygons = self.polygons
        with self.polygons_mutex:
            img_name = os.path.split(self.image_path)[-1]
            polygons_data = [
                {
                    "polygon": [[x // self.scale_factor, y // self.scale_factor] for x, y in polygon.pt_coords],
                    "label": polygon.text or "",
                    "type": polygon.poly_type or "words",
                }
                for polygon in polygons
                if polygon.pt_coords
            ]
            filtered_polygons = [entry["polygon"] for entry in polygons_data]
            labels = [entry["label"] for entry in polygons_data]
            types = [entry["type"] for entry in polygons_data]
            if len(filtered_polygons) != len(labels) != len(types):
                logger.error("Length of polygons, labels and types do not match")
                raise ValueError("Length of polygons, labels and types do not match")

            if not filtered_polygons:
                logger.warning("Not saving JSON as no polygons are present")
                return "--> Nothing to save, because no polygons are present"

            data = {
                img_name: {
                    "img_dimensions": [self.img_height, self.img_width],
                    "img_hash": self._get_img_hash(),
                    "polygons": filtered_polygons,
                    "labels": labels,
                    "types": types,
                }
            }

            json_file_path = os.path.join(self.tmp_labels_path, img_name.split(".")[0] + ".json")
            try:
                with open(json_file_path, "w", encoding="utf-8") as fl:
                    json.dump(data, fl, indent=4, ensure_ascii=False)
                logger.info(f"Successfully saved JSON to {json_file_path}")
            except Exception as e:  # pragma: no cover
                logger.error(f"Failed to save JSON: {e}")
                raise

            return str(json_file_path)

    def final_save(self):
        """
        Save the final labels to a json file
        """
        data = {}
        for fl in os.listdir(self.tmp_labels_path):
            with open(os.path.join(self.tmp_labels_path, fl), "r", encoding="utf-8") as fl:  # type: ignore[assignment]
                tmp_annotation = json.load(fl)  # type: ignore[arg-type]
                # update only if polygons are present
                if tmp_annotation[list(tmp_annotation.keys())[0]].get("polygons"):
                    data.update(tmp_annotation)
        with open(os.path.join(self.root_path, "labels.json"), "w", encoding="utf-8") as fl:  # type: ignore[assignment]
            json.dump(data, fl, indent=4, ensure_ascii=False)  # type: ignore[arg-type]
        logger.info(f"Finally saved to {os.path.join(self.root_path, 'labels.json')}")

    def draw_polys(self, coords: list[list[list[int]]], poly_types: list[str], poly_texts: list[str]):
        """ "
        Draw polygons on the canvas

        Args:
            coords: list[list[list[int]]]: List of polygons to draw
            poly_types: list[str]: List of polygon types
            poly_texts: list[str]: List of polygon texts
        """
        with self.polygons_mutex:
            # Scale coordinates and create polygons
            scaled_coords = [[[int(x * self.scale_factor) for x in point] for point in poly] for poly in coords]
            self.polygons.extend(
                Polygon(self.root, self.canvas, poly, poly_type, poly_text)
                for poly, poly_type, poly_text in zip(scaled_coords, poly_types, poly_texts)
            )
            # Update also the original coordinates for accurate scaling to the original image size
            for polygon in self.polygons:
                polygon.original_coords = [
                    [int(x // self.scale_factor), int(y // self.scale_factor)] for x, y in polygon.pt_coords
                ]

        logger.info(f"Total Polygons drawn: {len(self.polygons)}")

    def add_poly(self, pts: list[list[int]]):
        """
        Add a polygon to the canvas.

        Args:
            pts: list[list[int]]: List of points of the polygon.
        """
        scaled_pts = [[int(x * self.scale_factor), int(y * self.scale_factor)] for x, y in pts]
        polygon = Polygon(self.root, self.canvas, scaled_pts)
        polygon.original_coords = pts  # Store unscaled coordinates for accurate scaling
        self.polygons.append(polygon)
        logger.info(f"Added polygon. Total: {len(self.polygons)}")
