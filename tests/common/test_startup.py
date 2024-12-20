import pytest
from tkinter import TclError


@pytest.mark.xvfb
def test_gui_startup(gui_app):
    """Test if the GUI application starts without errors."""
    try:
        gui_app.update()
    except TclError:
        pytest.fail("GUI failed to start.")
