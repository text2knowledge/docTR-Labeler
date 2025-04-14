from unittest.mock import Mock, patch


def test_gui_initialization(gui_app):
    assert gui_app.title() == "docTR Labeler"
    assert gui_app.keep_drawing.get() is False
    assert gui_app.auto_tight_poly.get() is True
    assert gui_app.threshold_scale.get() == 128
    assert gui_app.type_variable.get() == gui_app.type_options[0]
    assert gui_app.label_text.get() == ""


def test_canvas_properties(gui_app):
    assert int(gui_app.canvas.cget("width")) > 0
    assert int(gui_app.canvas.cget("height")) > 0


def test_hide_buttons(gui_app):
    gui_app.hide_buttons()
    assert str(gui_app.load_image_directory_button["state"]) == "disabled"
    assert str(gui_app.jump_entry["state"]) == "disabled"
    assert str(gui_app.jump_button["state"]) == "disabled"
    assert str(gui_app.auto_annotate_button["state"]) == "disabled"
    assert str(gui_app.next_img_button["state"]) == "disabled"
    assert str(gui_app.save_image_button["state"]) == "disabled"
    assert str(gui_app.delete_poly_button["state"]) == "disabled"
    assert str(gui_app.deselect_all_button["state"]) == "disabled"
    assert str(gui_app.select_all_button["state"]) == "disabled"
    assert str(gui_app.draw_poly_button["state"]) == "disabled"
    assert str(gui_app.make_tight_button["state"]) == "disabled"
    assert str(gui_app.label_text["state"]) == "disabled"
    assert str(gui_app.label_type["state"]) == "disabled"


def test_show_buttons(gui_app):
    gui_app.show_buttons()
    assert str(gui_app.jump_entry["state"]) == "normal"
    assert str(gui_app.jump_button["state"]) == "normal"
    assert str(gui_app.auto_annotate_button["state"]) == "normal"
    assert str(gui_app.next_img_button["state"]) == "normal"
    assert str(gui_app.save_image_button["state"]) == "normal"
    assert str(gui_app.delete_poly_button["state"]) == "normal"
    assert str(gui_app.deselect_all_button["state"]) == "normal"
    assert str(gui_app.select_all_button["state"]) == "normal"
    assert str(gui_app.draw_poly_button["state"]) == "normal"
    assert str(gui_app.make_tight_button["state"]) == "normal"
    assert str(gui_app.label_text["state"]) == "normal"
    assert str(gui_app.label_type["state"]) == "normal"


def test_toggle_keep_drawing(gui_app):
    assert gui_app.keep_drawing.get() is False
    gui_app.keep_drawing.set(True)
    assert gui_app.keep_drawing.get() is True
    gui_app.keep_drawing.set(False)
    assert gui_app.keep_drawing.get() is False


def test_toggle_auto_tight_poly(gui_app):
    assert gui_app.auto_tight_poly.get() is True
    gui_app.auto_tight_poly.set(False)
    assert gui_app.auto_tight_poly.get() is False
    gui_app.auto_tight_poly.set(True)
    assert gui_app.auto_tight_poly.get() is True


def test_jump_to_image_validation(gui_app):
    gui_app.numeric_var.set("abc")  # Invalid input
    assert not gui_app._validate_numeric_input(gui_app.numeric_var.get())
    gui_app.numeric_var.set("123")  # Valid input
    assert gui_app._validate_numeric_input(gui_app.numeric_var.get())


def test_progress_bar_initial_state(gui_app):
    assert str(gui_app.progress_bar.grid_info()) == "{}"  # Hidden by default


def test_progress_bar_visibility(gui_app):
    gui_app.progress_bar.grid()  # Show progress bar
    assert str(gui_app.progress_bar.grid_info()) != "{}"
    gui_app.progress_bar.grid_remove()  # Hide progress bar
    assert str(gui_app.progress_bar.grid_info()) == "{}"


def test_type_variable_update(gui_app):
    initial_type = gui_app.type_variable.get()
    new_type = gui_app.type_options[1] if len(gui_app.type_options) > 1 else "custom_type"
    gui_app.type_variable.set(new_type)
    assert gui_app.type_variable.get() == new_type
    # Revert to initial type
    gui_app.type_variable.set(initial_type)
    assert gui_app.type_variable.get() == initial_type


def test_bindings_exist(gui_app):
    bindings = {
        "<Escape>": gui_app.deselect_all,
        "<Control-a>": gui_app.select_all,
        "<Control-t>": gui_app.make_tight,
        "<Control-r>": gui_app.discard_tight,
        "<Control-s>": gui_app.saver,
        "<Control-d>": gui_app.delete_selected,
    }
    for key, expected_func in bindings.items():
        # Get all bindings for the key
        bound_func = gui_app.bind(key)
        assert bound_func is not None, f"No binding found for key: {key}"
        # If specific logic needs to be checked, ensure it matches expected function names
        assert expected_func.__name__ in str(bound_func), f"Unexpected binding for key: {key}"


def test_supported_formats(gui_app):
    assert "jpg" in gui_app.supported_formats
    assert "png" in gui_app.supported_formats
    assert "tiff" not in gui_app.supported_formats  # Unsupported format


def test_hide_buttons_disables_buttons(gui_app):
    gui_app.show_buttons()  # Enable all buttons first
    gui_app.hide_buttons()  # Now hide them
    buttons = [
        gui_app.jump_entry,
        gui_app.jump_button,
        gui_app.auto_annotate_button,
        gui_app.next_img_button,
        gui_app.save_image_button,
        gui_app.delete_poly_button,
        gui_app.deselect_all_button,
        gui_app.select_all_button,
        gui_app.draw_poly_button,
        gui_app.make_tight_button,
        gui_app.label_text,
        gui_app.label_type,
    ]
    for button in buttons:
        assert str(button["state"]) == "disabled"


def test_show_buttons_enables_buttons(gui_app):
    gui_app.hide_buttons()  # Disable all buttons first
    gui_app.show_buttons()  # Now show them
    buttons = [
        gui_app.jump_entry,
        gui_app.jump_button,
        gui_app.auto_annotate_button,
        gui_app.next_img_button,
        gui_app.save_image_button,
        gui_app.delete_poly_button,
        gui_app.deselect_all_button,
        gui_app.select_all_button,
        gui_app.draw_poly_button,
        gui_app.make_tight_button,
        gui_app.label_text,
        gui_app.label_type,
    ]
    for button in buttons:
        assert str(button["state"]) == "normal"


def test_select_all(gui_app):
    gui_app.img_cnv = Mock()
    gui_app.img_cnv.polygons = [Mock(), Mock(), Mock()]

    gui_app.select_all()

    for poly in gui_app.img_cnv.polygons:
        poly.select_polygon.assert_called_once()


def test_deselect_all(gui_app):
    gui_app.img_cnv = Mock()
    gui_app.img_cnv.polygons = [Mock(), Mock(), Mock()]

    gui_app.deselect_all()

    for poly in gui_app.img_cnv.polygons:
        poly.deselect_poly.assert_called_once()


def test_save_label(gui_app):
    gui_app.img_cnv = Mock()
    gui_app.img_cnv.polygons_mutex = Mock()  # Mock the mutex
    gui_app.img_cnv.polygons_mutex.__enter__ = Mock()
    gui_app.img_cnv.polygons_mutex.__exit__ = Mock()

    gui_app.last_selected_polygon = "123"
    mock_polygon = Mock()
    mock_polygon.polygon_id = "123"
    mock_polygon.select_poly = True
    gui_app.img_cnv.polygons = [mock_polygon]
    gui_app.label_variable = Mock()
    gui_app.label_variable.get.return_value = " new_label "

    # Mock save_image_button and its configure method
    gui_app.save_image_button = Mock()
    gui_app.save_image_button.configure = Mock()

    gui_app.save_label()

    gui_app.img_cnv.polygons_mutex.__enter__.assert_called_once()
    assert mock_polygon.text == "new_label"
    assert not gui_app.img_cnv.current_saved
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")


def test_save_type(gui_app):
    gui_app.img_cnv = Mock()
    gui_app.img_cnv.polygons_mutex = Mock()  # Mock the mutex
    gui_app.img_cnv.polygons_mutex.__enter__ = Mock()
    gui_app.img_cnv.polygons_mutex.__exit__ = Mock()

    gui_app.last_selected_polygon = "123"
    mock_polygon = Mock()
    mock_polygon.polygon_id = "123"
    mock_polygon.select_poly = True
    gui_app.img_cnv.polygons = [mock_polygon]
    gui_app.type_variable = Mock()
    gui_app.type_variable.get.return_value = " polygon_type "

    gui_app.save_image_button = Mock()  # Mock the save_image_button
    gui_app.save_image_button.configure = Mock()  # Mock the configure method

    gui_app.save_type()

    gui_app.img_cnv.polygons_mutex.__enter__.assert_called_once()
    assert mock_polygon.poly_type == "polygon_type"
    assert not gui_app.img_cnv.current_saved
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")


def test_load_new_img(gui_app):
    gui_app.canvas = Mock()
    gui_app.save_image_button = Mock()
    gui_app.image_dir = "test_dir"
    gui_app.image_name = "test_image.png"
    gui_app.img_cnv = Mock()

    gui_app.curr_idx = 0
    gui_app.images_in_dir = ["test_image.png"]

    with (
        patch("os.path.join", return_value="test_path") as mock_join,
        patch("labeler.views.gui.ImageOnCanvas") as mock_image_on_canvas,
        patch("labeler.views.gui.logger") as mock_logger,
    ):
        gui_app.load_new_img()

        gui_app.canvas.delete.assert_called_once_with("all")
        gui_app.save_image_button.configure.assert_called_once_with(state="disabled")
        mock_join.assert_called_once_with("test_dir", "test_image.png")
        mock_image_on_canvas.assert_called_once_with(gui_app, gui_app.canvas, "test_path")
        mock_logger.info.assert_called_once_with("Loaded image: test_path")


def test_auto_annotate(gui_app):
    gui_app.progress_bar = Mock()
    gui_app.auto_annotate_button = Mock()
    gui_app.auto_annotate_button.configure = Mock()
    gui_app.hide_buttons = Mock()
    gui_app.show_buttons = Mock()
    gui_app.img_cnv = Mock()
    gui_app.save_image_button = Mock()  # Ensure save_image_button is mocked
    gui_app.save_image_button.configure = Mock()  # Mock its configure method

    # Simulate the _background_task directly
    def _background_task():
        gui_app.auto_annotate_button.configure(state="disabled")
        gui_app.hide_buttons()
        gui_app.img_cnv.auto_annotate()

        # Stop the progress bar and hide it (must be done on the main thread)
        gui_app.progress_bar.stop()
        gui_app.progress_bar.grid_remove()
        gui_app.show_buttons()

    # Patch threading.Thread so that the background task runs synchronously
    with patch("threading.Thread") as mock_thread:
        mock_thread.return_value.start = Mock(side_effect=_background_task)  # Directly run the task

        gui_app.auto_annotate()

    gui_app.progress_bar.grid.assert_called_once()
    gui_app.progress_bar.start.assert_called_once()
    gui_app.auto_annotate_button.configure.assert_called_once_with(state="disabled")
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")


def test_load_directory(gui_app):
    gui_app.image_dir = None
    gui_app.images_in_dir = []
    gui_app.show_buttons = Mock()
    gui_app.next_img = Mock()
    gui_app.load_image_directory_button = Mock()
    gui_app.cli_usage = True

    with (
        patch("labeler.views.gui.filedialog.askdirectory", return_value="test_dir") as mock_askdirectory,
        patch("os.listdir", return_value=["image1.png", "image2.jpg"]) as mock_listdir,
    ):
        gui_app.load_directory()

        mock_askdirectory.assert_called_once()
        mock_listdir.assert_called_once_with("test_dir")
        assert gui_app.image_dir == "test_dir"
        assert gui_app.images_in_dir == ["image1.png", "image2.jpg"]
        gui_app.show_buttons.assert_called_once()
        gui_app.next_img.assert_called_once()


def test_jump_to_image(gui_app):
    gui_app.jump_entry = Mock()
    gui_app.jump_entry.get.return_value = "2"
    gui_app.images_in_dir = ["image1.png", "image2.jpg"]
    gui_app.pop_up = Mock()
    gui_app.next_img = Mock()

    gui_app.jump_to_image()

    assert gui_app.curr_idx == 0
    gui_app.next_img.assert_called_once()


def test_delete_selected(gui_app):
    gui_app.img_cnv = Mock()
    mock_polygon1 = Mock()
    mock_polygon1.select_poly = True
    mock_polygon2 = Mock()
    mock_polygon2.select_poly = False
    gui_app.img_cnv.polygons = [mock_polygon1, mock_polygon2]

    gui_app.save_image_button = Mock()  # Mock the save_image_button
    gui_app.save_image_button.configure = Mock()  # Mock the configure method

    gui_app.delete_selected()

    mock_polygon1.delete_self.assert_called_once()
    assert gui_app.img_cnv.polygons == [mock_polygon2]
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")


def test_saver(gui_app, monkeypatch):
    gui_app.img_cnv = Mock()
    gui_app.img_cnv.save_json.return_value = "test_path"
    gui_app.save_image_button = Mock()
    monkeypatch.setattr(gui_app, "deselect_all", lambda: None)
    with patch("labeler.views.gui.logger") as mock_logger:
        gui_app.saver()

        gui_app.save_image_button.configure.assert_called_once_with(state="disabled")
        gui_app.img_cnv.save_json.assert_called_once()
        mock_logger.info.assert_any_call("Saving annotations for None")
        mock_logger.info.assert_any_call("Annotations saved to test_path")
        assert gui_app.img_cnv.current_saved


def test_make_tight(gui_app):
    gui_app.progress_bar = Mock()
    gui_app.auto_annotate_button = Mock()
    gui_app.auto_annotate_button.configure = Mock()
    gui_app.hide_buttons = Mock()
    gui_app.show_buttons = Mock()
    gui_app.img_cnv = Mock()
    gui_app.save_image_button = Mock()
    gui_app.save_image_button.configure = Mock()
    gui_app.threshold_scale = Mock()
    gui_app.threshold_scale.get.return_value = 0.5

    # Mock the polygons
    mock_polygon1 = Mock()
    mock_polygon1.select_poly = True
    mock_polygon2 = Mock()
    mock_polygon2.select_poly = True
    gui_app.img_cnv.polygons = [mock_polygon1, mock_polygon2]

    with patch("labeler.views.gui.TightBox") as mock_tight_box:
        mock_tight_box_instance = Mock()
        mock_tight_box.return_value = mock_tight_box_instance
        gui_app.make_tight()

    gui_app.progress_bar.grid.assert_called_once()
    gui_app.progress_bar.start.assert_called_once()
    gui_app.hide_buttons.assert_called_once()
    gui_app.show_buttons.assert_called_once()
    gui_app.auto_annotate_button.configure.assert_called_once_with(state="disabled")
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")
    mock_tight_box.assert_called_once_with(gui_app, gui_app.img_cnv, 0.5)
    mock_tight_box_instance.tight_box.assert_called_once()

    gui_app.img_cnv.polygons = [mock_polygon1]
    with patch("labeler.views.gui.TightBox") as mock_tight_box:
        mock_tight_box_instance = Mock()
        mock_tight_box.return_value = mock_tight_box_instance
        gui_app.make_tight()

    mock_tight_box.assert_called_with(gui_app, gui_app.img_cnv, 0.5)
    mock_tight_box_instance.tight_box.assert_called_once()


def test_discard_tight(gui_app):
    gui_app.progress_bar = Mock()
    gui_app.auto_annotate_button = Mock()
    gui_app.auto_annotate_button.configure = Mock()
    gui_app.hide_buttons = Mock()
    gui_app.show_buttons = Mock()
    gui_app.img_cnv = Mock()
    gui_app.save_image_button = Mock()
    gui_app.save_image_button.configure = Mock()

    mock_tight_box = Mock()
    gui_app.tight_box_obj = mock_tight_box  # Ensure tight_box_obj is set

    gui_app.discard_tight()

    assert gui_app.tight_box_obj is None  # Ensure tight_box_obj is reset after discard
    assert gui_app.img_cnv.current_saved is False  # Ensure current_saved is set to False

    mock_tight_box.discard_tight_box.assert_called_once()
    gui_app.save_image_button.configure.assert_called_once_with(state="normal")
