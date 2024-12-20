import os
from unittest.mock import patch

import pytest

from labeler.utils.hub_factory import _check_dataset_path


def test_valid_dataset_path():
    dataset_path = "/valid/dataset"
    images_folder_name = "images"

    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda path: path in [
            dataset_path,
            os.path.join(dataset_path, images_folder_name),
            os.path.join(dataset_path, "labels.json"),
        ]

        # Should not raise any exception
        _check_dataset_path(dataset_path, images_folder_name)


def test_dataset_path_does_not_exist():
    dataset_path = "/invalid/dataset"
    images_folder_name = "images"

    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match=f"Dataset path {dataset_path} does not exist"):
            _check_dataset_path(dataset_path, images_folder_name)


def test_images_folder_missing():
    dataset_path = "/valid/dataset"
    images_folder_name = "images"

    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda path: path in [
            dataset_path,
            os.path.join(dataset_path, "labels.json"),
        ]

        with pytest.raises(FileNotFoundError, match=f"Dataset path {dataset_path} does not contain an 'images' folder"):
            _check_dataset_path(dataset_path, images_folder_name)


def test_labels_and_tmp_annotations_missing():
    dataset_path = "/valid/dataset"
    images_folder_name = "images"

    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda path: path in [
            dataset_path,
            os.path.join(dataset_path, images_folder_name),
        ]

        with pytest.raises(
            FileNotFoundError,
            match=f"Dataset path {dataset_path} does not contain a 'labels.json' file or a 'tmp_annotations' folder",
        ):
            _check_dataset_path(dataset_path, images_folder_name)
