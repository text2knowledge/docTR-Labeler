from io import BytesIO

import pytest
import requests
from onnxtr.utils.fonts import get_font
from PIL import Image, ImageDraw
from tkinter import TclError

from labeler.views.gui import GUI


@pytest.fixture
def gui_app():
    """Fixture to initialize the GUI application."""
    app = GUI()
    yield app
    try:
        app.destroy()
    except TclError:
        pass  # Already destroyed


def synthesize_text_img(
    text: str,
    font_size: int = 32,
    font_family=None,
    background_color=None,
    text_color=None,
) -> Image.Image:
    background_color = (0, 0, 0) if background_color is None else background_color
    text_color = (255, 255, 255) if text_color is None else text_color

    font = get_font(font_family, font_size)
    left, top, right, bottom = font.getbbox(text)
    text_w, text_h = right - left, bottom - top
    h, w = int(round(1.3 * text_h)), int(round(1.1 * text_w))
    # If single letter, make the image square, otherwise expand to meet the text size
    img_size = (h, w) if len(text) > 1 else (max(h, w), max(h, w))

    img = Image.new("RGB", img_size[::-1], color=background_color)
    d = ImageDraw.Draw(img)

    # Offset so that the text is centered
    text_pos = (int(round((img_size[1] - text_w) / 2)), int(round((img_size[0] - text_h) / 2)))
    # Draw the text
    d.text(text_pos, text, font=font, fill=text_color)
    return img


@pytest.fixture(scope="session")
def mock_pdf(tmpdir_factory):
    # Page 1
    text_img = synthesize_text_img("I am a jedi!", background_color=(255, 255, 255), text_color=(0, 0, 0))
    page = Image.new(text_img.mode, (1240, 1754), (255, 255, 255))
    page.paste(text_img, (50, 100))

    # Page 2
    text_img = synthesize_text_img("No, I am your father.", background_color=(255, 255, 255), text_color=(0, 0, 0))
    _page = Image.new(text_img.mode, (1240, 1754), (255, 255, 255))
    _page.paste(text_img, (40, 300))

    # Save the PDF
    fn = tmpdir_factory.mktemp("data").join("mock_pdf_file.pdf")
    page.save(str(fn), "PDF", save_all=True, append_images=[_page])

    return str(fn)


@pytest.fixture(scope="session")
def mock_payslip(tmpdir_factory):
    url = "https://3.bp.blogspot.com/-Es0oHTCrVEk/UnYA-iW9rYI/AAAAAAAAAFI/hWExrXFbo9U/s1600/003.jpg"
    file = BytesIO(requests.get(url).content)
    folder = tmpdir_factory.mktemp("data")
    fn = str(folder.join("mock_payslip.jpeg"))
    with open(fn, "wb") as f:
        f.write(file.getbuffer())
    return fn


@pytest.fixture(scope="session")
def mock_text_box_stream():
    url = "https://doctr-static.mindee.com/models?id=v0.5.1/word-crop.png&src=0"
    return requests.get(url).content


@pytest.fixture(scope="session")
def mock_text_box(mock_text_box_stream, tmpdir_factory):
    file = BytesIO(mock_text_box_stream)
    fn = tmpdir_factory.mktemp("data").join("mock_text_box_file.png")
    with open(fn, "wb") as f:
        f.write(file.getbuffer())
    return str(fn)


@pytest.fixture(scope="session")
def mock_mixed_data_folder(tmpdir_factory):
    temp_folder = tmpdir_factory.mktemp("data")
    # Page 1
    text_img = synthesize_text_img("I am a jedi!", background_color=(255, 255, 255), text_color=(0, 0, 0))
    page = Image.new(text_img.mode, (1240, 1754), (255, 255, 255))
    page.paste(text_img, (50, 100))
    # Save the PDF
    pdf_fn = temp_folder.join("mock_pdf_file.pdf")
    page.save(str(pdf_fn), "PDF", save_all=True)

    # Image
    url = "https://3.bp.blogspot.com/-Es0oHTCrVEk/UnYA-iW9rYI/AAAAAAAAAFI/hWExrXFbo9U/s1600/003.jpg"
    file = BytesIO(requests.get(url).content)
    img_fn = str(temp_folder.join("mock_payslip.jpeg"))
    with open(img_fn, "wb") as f:
        f.write(file.getbuffer())
    return str(temp_folder)
