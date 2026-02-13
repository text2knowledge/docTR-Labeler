import json
import os
from unittest.mock import MagicMock, mock_open, patch

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
    mock_polygon = MagicMock(pt_coords=[[0, 0], [10, 0], [10, 10], [0, 10]], text="label", poly_type="words")
    image_on_canvas.polygons = [mock_polygon]
    image_on_canvas.root.type_options = ["words"]
    image_on_canvas.root.color_palette = ["#FF0000"]
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


def test_load_json_invalid_type_fallback_color(image_on_canvas, mock_annotation_data):
    json_content = json.dumps(mock_annotation_data)
    image_on_canvas.image_path = "/some/path/mock_image.jpg"
    image_on_canvas.root.type_options = ["unknown_type"]
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json_content)),
        patch.object(image_on_canvas, "draw_polys") as mock_draw,
    ):
        image_on_canvas.load_json()
        mock_draw.assert_called_once()
        passed_colors = mock_draw.call_args[0][3]
        assert passed_colors == ["#808080"]
    assert image_on_canvas.drawing_polygon is False


def test_load_json_color_mapping(image_on_canvas, mock_annotation_data):
    image_on_canvas.image_path = "mock_image.jpg"
    image_on_canvas.root.type_options = ["words", "document_type", "invoice_id"]
    image_on_canvas.root.color_palette = ["#FF0000", "#00FF00", "#0000FF"]
    # image_on_canvas.root.type_options = ["words", "header", "footer"]
    # test_palette = ["#FF0000", "#00FF00", "#0000FF"]
    # image_on_canvas.root.color_palette = test_palette
    # mock_annotation_data["mock_image.jpg"]["colors"] = test_palette
    mock_annotation_data["mock_image.jpg"]["types"] = ["document_type", "invoice_id"]
    json_content = json.dumps(mock_annotation_data)

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json_content)),
        patch.object(image_on_canvas, "draw_polys") as mock_draw_polys,
    ):
        image_on_canvas.load_json()
        mock_draw_polys.assert_called_once()
        actual_types = mock_draw_polys.call_args[0][1]
        assert actual_types == ["document_type", "invoice_id"]
        actual_colors = mock_draw_polys.call_args[0][3]
        assert actual_colors == ["#00FF00", "#0000FF"]
        assert len(actual_colors) == len(actual_types)
