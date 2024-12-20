from unittest.mock import MagicMock, patch

import pytest

from labeler.utils.data_utils import prepare_data_folder


def test_prepare_data_folder_valid():
    data_folder = "/valid/data"
    save_folder = "/valid/images"
    mock_files = ["file1.pdf", "file2.jpg"]

    with (
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.listdir", return_value=mock_files),
        patch("labeler.utils.data_utils.DocumentFile.from_pdf", return_value=[[MagicMock()]]),
        patch("labeler.utils.data_utils.DocumentFile.from_images", return_value=[[MagicMock()]]),
        patch("PIL.Image.fromarray"),
        patch("hashlib.sha256") as mock_sha256,
    ):
        mock_exists.side_effect = lambda path: path == data_folder
        mock_sha256().hexdigest.return_value = "mockhash"

        result = prepare_data_folder(data_folder)

        # Assertions
        mock_makedirs.assert_called_once_with(save_folder)
        assert result == save_folder


def test_prepare_data_folder_missing_data_folder():
    data_folder = "/invalid/data"

    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match=f"Data folder {data_folder} does not exist"):
            prepare_data_folder(data_folder)


def test_prepare_data_folder_existing_save_folder():
    data_folder = "/valid/data"
    save_folder = "/valid/images"

    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda path: path in [data_folder, save_folder]

        with pytest.raises(FileExistsError, match=f"Save folder {save_folder} already exists please remove it first"):
            prepare_data_folder(data_folder)


def test_prepare_data_folder_unsupported_file():
    data_folder = "/valid/data"
    save_folder = "/valid/images"
    mock_files = ["unsupported.txt"]

    with (
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.listdir", return_value=mock_files),
    ):
        mock_exists.side_effect = lambda path: path == data_folder

        result = prepare_data_folder(data_folder)

        # Assertions
        mock_makedirs.assert_called_once_with(save_folder)
        assert result == save_folder


def test_prepare_data_folder_processing_error():
    data_folder = "/valid/data"
    save_folder = "/valid/images"
    mock_files = ["file1.pdf"]

    with (
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.listdir", return_value=mock_files),
        patch("labeler.utils.data_utils.DocumentFile.from_pdf", side_effect=Exception("Mock error")),
    ):
        mock_exists.side_effect = lambda path: path == data_folder

        result = prepare_data_folder(data_folder)

        mock_makedirs.assert_called_once_with(save_folder)
        assert result == save_folder
