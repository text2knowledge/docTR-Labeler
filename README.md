<p align="center">
  <img src="https://github.com/text2knowledge/docTR-Labeler/raw/main/docs/images/logo.png" width="40%">
</p>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![Build Status](https://github.com/text2knowledge/docTR-Labeler/workflows/builds/badge.svg)
[![codecov](https://codecov.io/gh/text2knowledge/docTR-Labeler/graph/badge.svg?token=vrRnHbweMg)](https://codecov.io/gh/text2knowledge/docTR-Labeler)
[![CodeFactor](https://www.codefactor.io/repository/github/text2knowledge/doctr-labeler/badge)](https://www.codefactor.io/repository/github/text2knowledge/doctr-labeler)
[![Pypi](https://img.shields.io/badge/pypi-v0.1.3-blue.svg)](https://pypi.org/project/docTR-Labeler/)

docTR Labeler is a tool to label OCR data for the [docTR](https://github.com/mindee/doctr) and [OnnxTR](https://github.com/felixdittrich92/OnnxTR) projects.

**Attention**: This project is still in development - and currently a pre-release version - please report any issues you encounter.

What you can expect from this repository:

- Efficient way to label OCR data
- Features like auto-annotation using [OnnxTR](https://github.com/felixdittrich92/OnnxTR) and auto polygon adjustment
- Easy to use frontend with keybindings
- CLI and programmatic usage
- No Login required

<p align="center">
  <img src="https://github.com/text2knowledge/docTR-Labeler/raw/main/docs/images/ui_screen.png" width="90%">
</p>

## Installation

### Prerequisites

Python 3.10 (or higher) and [pip](https://pip.pypa.io/en/stable/) are required to install docTR-Labeler.

### Latest release

You can then install the latest release of the package using [pypi](https://pypi.org/project/OnnxTR/) as follows:

```bash
pip3 install doctr-labeler
```

## Keybindings

- `Ctrl + a` : Select all polygons
- `Esc` : Deselect all selected polygons
- `Ctrl + t` : Auto adjust the selected polygons
- `Ctrl + r` : Reset last auto adjustment
- `Ctrl + s` : Save the current progress / image annotation
- `Ctrl + d` : Delete the selected polygon
- `Ctrl + f` : Draw a new polygon
- `Ctrl + c` : Undo while drawing a polygon

- `Ctrl + +` : Zoom in (up to 150% by default) - Can be changed by setting a environment variable `DOCTR_LABELER_MAX_ZOOM` to a value between 1.1 and 2.0
- `Ctrl + -` : Zoom out (down to 50% by default) - Can be changed by setting a environment variable `DOCTR_LABELER_MIN_ZOOM` to a value between 0.1 and 0.9

## Configuration

You can set the following environment variables to configure the tool:

- `DOCTR_LABELER_MAX_ZOOM` : Maximum zoom level (default: 1.5)
- `DOCTR_LABELER_MIN_ZOOM` : Minimum zoom level (default: 0.5)
- `RECOGNITION_ARCH` : The recognition architecture to use (default: `Felix92/onnxtr-parseq-multilingual-v1`)
- `DETECTION_ARCH` : The detector architecture to use (default: `fast_base`)
- `OBJECTNESS_THRESHOLD` : The objectness threshold for the detector (default: 0.5)

## Usage CLI

After installation you can use the CLI to start the tool:

For this open a terminal and run:

```bash
doctr-labeler
```

## Usage Programmatic

You can also use the tool programmatic:

```python
from labeler.views import GUI
from labeler.utils import prepare_data_folder, hf_upload_dataset

# (Optional)
# Prepare the data folder you can pass a path to a folder containing images and PDFs
# The function will create a new folder 'images' with the prepared data
prepared_data_path = prepare_data_folder("path/to/folder")

# Start the GUI
gui = GUI(image_folder=prepared_data_path)
gui.start_gui()

# or if you want to annotate also for KIE
types = ["Total", "Date", "Invoice Number", "VAT Number", "Address", "Company Name"]
gui = GUI(image_folder=prepared_data_path, text_types=types)
gui.start_gui()

# (Optional) Upload the prepared data to the Hugging Face dataset hub
# The path to the folder should contain an 'images' folder and it's corresponding 'labels.json' file or the 'tmp
hf_upload_dataset(prepared_data_path)
```

## Credits

- This project is based on the [Form-Labeller](https://github.com/devarshi16/Form-Labeller) project by Devarshi Aggarwal.

## Citation

If you wish to cite please refer to the base project citation, feel free to use this [BibTeX](http://www.bibtex.org/) references:

```bibtex
@misc{docTR-Labeler,
    title={docTR Labeler: docTR OCR Annotation Tool},
    author={{Dittrich, Felix}, {List, Ian}},
    year={2024},
    publisher = {GitHub},
    howpublished = {\url{https://github.com/text2knowledge/docTR-Labeler}}
}
```

```bibtex
@misc{Form-Labeller,
  author = {Aggarwal, Devarshi},
  title = {{Form Labeller}},
  howpublished = {\url{https://github.com/devarshi16/Form-Labeller}},
  year = {2020},
  note = {Online; accessed 01-March-2020}
}
```

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create.

Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Add your Changes
4. Run the tests and quality checks (`make test` and `make style` and `make quality`)
5. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the Branch (`git push origin feature/AmazingFeature`)

## License

Distributed under the Apache 2.0 License. See [`LICENSE`](https://github.com/felixdittrich92/OnnxTR?tab=Apache-2.0-1-ov-file#readme) for more information.
