from .auto_labeler import AutoLabeler
from .tight_box import TightBox

__all__ = ["auto_annotator", "TightBox"]

# Init the AutoLabeler class once into RAM / GPU
auto_annotator = AutoLabeler()
