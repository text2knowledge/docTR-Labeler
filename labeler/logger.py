# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from logging import INFO, FileHandler, Formatter, Logger, StreamHandler, _nameToLevel, getLogger

__all__ = ["logger"]


def get_logger(mode: str = "INFO") -> Logger:
    """
    Returns a logger to use for the entire module.

    Args:
        mode: str: The logging level to use. Defaults to "INFO".

    Returns:
        Logger-Object with a unified name for the module.
    """
    log = getLogger("doctr-labeler-logger")
    log.setLevel(_nameToLevel.get(mode, INFO))

    file_handler = FileHandler("doctr-labeler.log")
    stream_handler = StreamHandler()

    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)

    return log


logger = get_logger()
