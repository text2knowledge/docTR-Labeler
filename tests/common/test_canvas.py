import os
from unittest.mock import MagicMock, patch

import pytest

from labeler.views import ImageOnCanvas


@pytest.fixture
def mock_canvas():
    mock_canvas = MagicMock()
    mock_canvas.winfo_width.return_value = 800
    mock_canvas.winfo_height.return_value = 600
    mock_canvas.create_image.return_value = "mock_canvas_image"
    return mock_canvas


@pytest.fixture
def mock_image():
    mock_image = MagicMock()
    mock_image.size = (1024, 768)
    mock_image.mode = "RGB"
    return mock_image


@pytest.fixture
def image_on_canvas(mock_canvas, mock_image, mock_payslip):
    with patch("PIL.Image.open", return_value=mock_image), patch("PIL.ImageTk.PhotoImage", return_value="mock_imagetk"):
        root = MagicMock()
        image_path = mock_payslip
        return ImageOnCanvas(root, mock_canvas, image_path)


def test_current_state(image_on_canvas):
    polygons, drawing_status = image_on_canvas.current_state()
    assert polygons == []
    assert drawing_status is False


def test_save_json(image_on_canvas):
    mock_polygon = MagicMock(pt_coords=[[0, 0], [10, 0], [10, 10], [0, 10]], text="label", poly_type="type")
    image_on_canvas.polygons = [mock_polygon]

    with (
        patch("os.makedirs") as mock_makedirs,
        patch("hashlib.sha256", return_value=MagicMock(hexdigest=lambda: "mockhash")),
        patch("builtins.open", MagicMock()) as mock_open,
    ):
        json_path = image_on_canvas.save_json()
        assert json_path == os.path.join(image_on_canvas.tmp_labels_path, "mock_payslip.json")
        mock_makedirs.assert_called_once_with(image_on_canvas.tmp_labels_path)
        mock_open.assert_any_call(
            os.path.join(image_on_canvas.tmp_labels_path, "mock_payslip.json"), "w", encoding="utf-8"
        )


def test_auto_annotate(image_on_canvas):
    mock_predictions = {"polygons": [[[0, 0], [10, 0], [10, 10], [0, 10]]], "texts": ["sample text"]}
    with (
        patch("labeler.automation.auto_annotator.predict", return_value=mock_predictions),
        patch.object(image_on_canvas, "draw_polys") as mock_draw_polys,
    ):
        image_on_canvas.auto_annotate()
        mock_draw_polys.assert_called_once_with(
            mock_predictions["polygons"], [image_on_canvas.root.type_options[0]], mock_predictions["texts"]
        )


def test_add_polygon(image_on_canvas):
    image_on_canvas.add_poly([[10, 10], [20, 20]])
    assert len(image_on_canvas.polygons) == 1


@patch("PIL.ImageTk.PhotoImage")  # Patch this to prevent error in zoom
def test_zoom_behavior(mock_photoimage, image_on_canvas):
    image_on_canvas.scale_factor = 1.0
    os.environ["DOCTR_LABELER_MAX_ZOOM"] = "1.5"
    os.environ["DOCTR_LABELER_MIN_ZOOM"] = "0.5"

    # Simulate zoom in
    image_on_canvas.zoom(MagicMock(keysym="plus"))

    # Simulate zoom out
    image_on_canvas.zoom(MagicMock(keysym="minus"))


def test_auto_label_sets_text(image_on_canvas):
    polygon = MagicMock(original_coords=[[0, 0], [10, 10]])
    with patch("labeler.automation.auto_annotator.predict_label", return_value="predicted"):
        image_on_canvas.auto_label(polygon)
        assert polygon.text == "predicted"


def test_save_json_empty_polygons_returns_message(image_on_canvas):
    image_on_canvas.polygons = []
    result = image_on_canvas.save_json()
    assert result.startswith("--> Nothing to save")
