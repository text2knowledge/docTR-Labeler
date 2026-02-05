# Copyright (C) 2024-2026, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import os
import subprocess
import textwrap
from uuid import uuid4

from huggingface_hub import HfApi, get_token, login

from ..logger import logger

__all__ = ["hf_upload_dataset"]


def login_to_hub() -> None:  # pragma: no cover
    """Login to huggingface hub"""
    access_token = get_token()
    if access_token is not None:
        logger.info("Huggingface Hub token found and valid")
        login(token=access_token)
    else:
        login()
    # check if git lfs is installed
    try:
        subprocess.call(["git", "lfs", "version"])
    except FileNotFoundError:
        raise OSError(
            "Looks like you do not have git-lfs installed, please install. \
                      You can install from https://git-lfs.github.com/. \
                      Then run `git lfs install` (you only have to do this once)."
        )


def _check_dataset_path(dataset_path: str, images_folder_name: str) -> None:
    """Check if the dataset path is valid"""
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset path {dataset_path} does not exist")
        raise FileNotFoundError(f"Dataset path {dataset_path} does not exist")

    if not os.path.exists(os.path.join(dataset_path, images_folder_name)):
        logger.error(f"Dataset path {dataset_path} does not contain an 'images' folder")
        raise FileNotFoundError(f"Dataset path {dataset_path} does not contain an 'images' folder")

    if not (
        os.path.exists(os.path.join(dataset_path, "labels.json"))
        or os.path.exists(os.path.join(dataset_path, "tmp_annotations"))
    ):
        logger.error(f"Dataset path {dataset_path} does not contain a 'labels.json' file or a 'tmp_annotations' folder")
        raise FileNotFoundError(
            f"Dataset path {dataset_path} does not contain a 'labels.json' file or a 'tmp_annotations' folder"
        )


def hf_upload_dataset(  # pragma: no cover
    dataset_path: str,
    images_folder_name: str = "images",
    dataset_name: str = f"docTR-OCR-dataset-{uuid4()}",
    dataset_description: str = "OCR dataset for docTR",
    dataset_tags: list[str] = ["ocr", "document", "labeling"],
    override: bool = False,
):
    """
    Upload a dataset to the Hugging Face Hub.

    Args:
        dataset_path: str: The path to the folder which contains the 'images' folder
        and 'labels.json' file or 'tmp_annotations' folder
        images_folder_name: str: The name of the folder containing the images (default: 'images')
        dataset_name: str: The name for the Hub dataset
        dataset_description: str: The description of the dataset
        dataset_tags: list[str]: The tags for the dataset (default: ['ocr', 'document', 'labeling'])
        override: bool: Whether to override an existing dataset with the same name
    """
    _check_dataset_path(dataset_path, images_folder_name)

    login_to_hub()

    # README
    tags_block = "\n".join(f"- {tag}" for tag in dataset_tags)
    readme = textwrap.dedent(
        f"""
        ---
        tags:
        {tags_block}
        license: apache-2.0
        ---

        <p align="center">
        <img src="https://github.com/felixdittrich92/docTR-Labeler/raw/main/docs/images/logo.jpg" width="40%">
        </p>

        **This OCR dataset was created with:**

        https://github.com/felixdittrich92/docTR-Labeler

        Description: {dataset_description}
        """
    ).strip()

    api = HfApi()

    # Create or reuse dataset repo
    repo_id = api.create_repo(
        repo_id=dataset_name,
        repo_type="dataset",
        exist_ok=override,
    )

    # Upload images
    api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=os.path.join(dataset_path, images_folder_name),
        path_in_repo="images",
    )

    # Upload annotations
    labels_path = os.path.join(dataset_path, "labels.json")
    if os.path.exists(labels_path):
        api.upload_file(
            repo_id=repo_id,
            repo_type="dataset",
            path_or_fileobj=labels_path,
            path_in_repo="labels.json",
        )

    tmp_ann_path = os.path.join(dataset_path, "tmp_annotations")
    if os.path.exists(tmp_ann_path):
        api.upload_folder(
            repo_id=repo_id,
            repo_type="dataset",
            folder_path=tmp_ann_path,
            path_in_repo="tmp_annotations",
        )

    # Upload README
    readme_path = os.path.join(dataset_path, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    api.upload_file(
        repo_id=repo_id,
        repo_type="dataset",
        path_or_fileobj=readme_path,
        path_in_repo="README.md",
    )

    logger.info(f"Dataset uploaded to Hugging Face Hub: {repo_id}")
