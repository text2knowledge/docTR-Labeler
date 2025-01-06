# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import hashlib
import os
import tempfile

from onnxtr.io import DocumentFile
from PIL import Image
from tqdm import tqdm

from labeler.logger import logger

__all__ = ["prepare_data_folder"]


def prepare_data_folder(data_folder: str) -> str:
    """
    Prepare the data folder for the labeler

    Args:
        data_folder: str: The path to the data folder which contains PDF and / or image files

    Returns:
        str: The path to the prepared data folder
    """
    # Check that the folder exists otherwsie raise an error
    if not os.path.exists(data_folder):
        logger.error(f"Data folder {data_folder} does not exist")
        raise FileNotFoundError(f"Data folder {data_folder} does not exist")

    save_folder = os.path.join(os.path.dirname(data_folder), "images")

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    else:
        logger.error(f"Save folder {save_folder} already exists")
        raise FileExistsError(f"Save folder {save_folder} already exists please remove it first")

    for file in tqdm(iterable=os.listdir(data_folder), desc="Processing files", total=len(os.listdir(data_folder))):
        try:
            file_path = os.path.join(data_folder, file)
            if file.lower().endswith(".pdf"):
                # Convert the PDF file to images
                images = DocumentFile.from_pdf(file_path)
                logger.info(f"Converted {file_path} to images")
            elif file.lower().endswith((".jpg", ".jpeg", ".png")):
                # Convert the image file to a list with one element
                images = DocumentFile.from_images([file_path])
                logger.info(f"Added {file_path} to the list of images")
            else:
                # Skip unsupported file types
                logger.warning(f"Skipping unsupported file type {file}")
                continue

            # Process each image immediately
            for img_array in images:
                with tempfile.NamedTemporaryFile() as tmp:
                    img = Image.fromarray(img_array)
                    img.save(tmp.name, "PNG")
                    tmp.seek(0)  # Move to the start of the file for hashing
                    sha256 = hashlib.sha256(tmp.read()).hexdigest()
                    # Save the image with its hash as the filename
                    img.save(os.path.join(save_folder, f"{sha256}.png"), "PNG")
        except Exception as e:
            logger.error(f"Error while processing {file}: {e}")

    return save_folder
