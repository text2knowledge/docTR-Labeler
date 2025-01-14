# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

from ..views.gui import GUI


def main():
    """
    Main entry point for the labeler CLI.
    """
    gui = GUI(cli=True)
    gui.start_gui()


if __name__ == "__main__":
    main()
