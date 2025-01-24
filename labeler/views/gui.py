# Copyright (C) 2024-2025, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import os
import threading

import darkdetect
import sv_ttk
import tkinter as tk
from tkinter import filedialog, ttk

from ..automation import TightBox
from ..components import DrawPoly
from ..logger import logger
from .canvas import ImageOnCanvas

__all__ = ["GUI"]


class GUI(tk.Tk):
    """
    The main window for the docTR Labeler application.

    Keyword Args:
        text_types (list): A list of text types to be used for labeling. Default is ["words"].
        image_folder (str): The path to the folder containing images. Default is None.
        cli (bool): A flag to indicate if the GUI is being used in CLI mode. Default is False.
    """

    def __init__(self, *args, **kwargs):
        text_types = kwargs.get("text_types", ["words"])
        self.image_folder = kwargs.get("image_folder", None)
        self.cli_usage = kwargs.get("cli", False)
        # Set default type which should be "words"
        self.type_options = text_types if "words" in text_types else ["words"] + text_types
        kwargs.pop("text_types", None)
        kwargs.pop("image_folder", None)
        kwargs.pop("cli", None)
        super().__init__(*args, **kwargs)

        # configure window
        self.title("docTR Labeler")
        self.button_width = 26

        # Add a BooleanVar to track the "Keep Drawing" mode
        self.keep_drawing = tk.BooleanVar(value=False)
        self.auto_tight_poly = tk.BooleanVar(value=True)
        self.numeric_var = tk.StringVar(self, "1")
        vcmd = (self.register(self._validate_numeric_input), "%P")

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.maxsize(screen_width, screen_height)
        self.supported_formats = ["jpg", "png"]

        # Key bindings
        self.bind("<Escape>", self.deselect_all)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Control-t>", self.make_tight)
        self.bind("<Control-r>", self.discard_tight)
        self.bind("<Control-s>", self.saver)
        self.bind("<Control-d>", self.delete_selected)
        self.bind("<Control-f>", self.draw_poly_func)
        self.bind("<Control-c>", self.discard_drawing)

        self.image_name: str | None = None
        self.image_dir: str | None = self.image_folder
        self.images_in_dir: list[str] = []
        self.curr_idx: int | None = None
        self.img_cnv: ImageOnCanvas | None = None
        self.drawing_obj: DrawPoly | None = None
        self.tight_box_obj: TightBox | None = None

        # Frames
        self.left_frame = ttk.Frame(self)
        self.top_frame = ttk.Frame(self.left_frame)
        self.bottom_frame = ttk.Frame(self)

        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_rowconfigure(0, weight=1)

        # Bar Buttons
        self.load_image_directory_button = ttk.Button(
            self.top_frame,
            text="Open Folder",
            command=self.load_directory,
            width=self.button_width,
        )
        # Jump to Image Section
        self.jump_entry = ttk.Entry(
            self.top_frame,
            width=self.button_width // 2,
            font=("Arial", 7),
            textvariable=self.numeric_var,
            validatecommand=vcmd,
        )
        self.jump_button = ttk.Button(
            self.top_frame,
            text="Go to Image",
            command=self.jump_to_image,
            width=self.button_width // 2,
        )
        self.auto_annotate_button = ttk.Button(
            self.top_frame,
            text="AUTO ANNOTATE",
            command=self.auto_annotate,
            width=self.button_width,
        )
        self.prev_img_button = ttk.Button(
            self.top_frame,
            text="← Prev",
            command=self.previous_img,
            state="disabled",
            width=self.button_width // 2,
        )
        self.next_img_button = ttk.Button(
            self.top_frame,
            text="Next → ",
            command=self.next_img,
            width=self.button_width // 2,
        )
        self.save_image_button = ttk.Button(
            self.top_frame,
            text="Save ",
            command=self.saver,
            width=self.button_width,
        )
        self.keep_drawing_checkbox = ttk.Checkbutton(
            self.top_frame,
            text="Keep Drawing Mode",
            variable=self.keep_drawing,
            width=self.button_width,
        )
        self.draw_poly_button = ttk.Button(
            self.top_frame,
            text="Draw Poly",
            command=self.draw_poly_func,
            width=self.button_width,
        )
        self.delete_poly_button = ttk.Button(
            self.top_frame,
            text="Delete Selected",
            command=self.delete_selected,
            width=self.button_width,
        )
        self.select_all_button = ttk.Button(
            self.top_frame,
            text="Select All",
            command=self.select_all,
            width=self.button_width,
        )
        self.deselect_all_button = ttk.Button(
            self.top_frame,
            text="Deselect All",
            command=self.deselect_all,
            width=self.button_width,
        )
        self.make_tight_button = ttk.Button(
            self.top_frame,
            text="Make Tight",
            command=self.make_tight,
            width=self.button_width,
        )
        self.threshold_label = ttk.Label(self.top_frame, text="Threshold", width=self.button_width)
        self.threshold_scale = ttk.Scale(
            self.top_frame,
            from_=0,
            to=255,
            orient="horizontal",
            length=self.button_width,
        )
        self.threshold_scale.set(128)
        self.auto_tight_poly_checkbutton = ttk.Checkbutton(
            self.top_frame,
            text="Auto Adjust Polys",
            variable=self.auto_tight_poly,
            width=self.button_width,
        )
        self.label_text_header = ttk.Label(self.top_frame, text="Text label (optional)", width=self.button_width)
        self.label_variable = tk.StringVar(self.top_frame, "")
        # Listener for label text
        self.label_variable.trace_add("write", lambda *args: self.save_label())
        self.label_text = ttk.Entry(
            self.top_frame, width=self.button_width, font=("Arial", 14), textvariable=self.label_variable
        )
        self.label_text.insert("end", "")

        self.label_type_header = ttk.Label(self.top_frame, text="Text type (optional)", width=self.button_width)
        self.type_variable = tk.StringVar(self.top_frame, self.type_options[0])
        # Listener for label type
        self.type_variable.trace_add("write", lambda *args: self.save_type())
        self.label_type = ttk.OptionMenu(
            self.top_frame, self.type_variable, self.type_variable.get(), *self.type_options
        )
        self.progress_bar = ttk.Progressbar(self.top_frame, orient="horizontal", length=100, mode="determinate")

        # Canvas
        self.canvas = tk.Canvas(
            self.bottom_frame, width=screen_width - self.top_frame.winfo_width(), height=screen_height, borderwidth=1
        )
        self.hbar = ttk.Scrollbar(self.bottom_frame, orient="horizontal")
        self.vbar = ttk.Scrollbar(self.bottom_frame, orient="vertical")

        # Bind the mouse wheel to the canvas
        def _on_mouse_wheel(event):  # pragma: no cover
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        # For Windows and MacOS
        self.canvas.bind("<MouseWheel>", _on_mouse_wheel)
        # For Linux (bind scroll up and down)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # Configure Grid
        self.load_image_directory_button.grid(row=0, columnspan=2, padx=20, pady=10, sticky="we")
        # Remove the button if an image folder is already set
        if self.image_folder:  # pragma: no cover
            self.load_image_directory_button.grid_remove()

        self.jump_entry.grid(row=1, column=0, padx=(20, 10), pady=(5, 20), sticky="we")
        self.jump_button.grid(row=1, column=1, padx=(10, 20), pady=(5, 20), sticky="we")

        self.auto_annotate_button.grid(row=2, columnspan=2, padx=20, pady=20, sticky="we")

        self.prev_img_button.grid(row=3, column=0, padx=5, pady=(15, 10), sticky="we")
        self.next_img_button.grid(row=3, column=1, padx=5, pady=(15, 10), sticky="we")
        self.save_image_button.grid(row=4, columnspan=2, padx=5, pady=(10, 50), sticky="we")

        self.keep_drawing_checkbox.grid(row=5, columnspan=2, padx=5, pady=10, sticky="we")
        self.draw_poly_button.grid(row=6, columnspan=2, padx=5, pady=10, sticky="we")
        self.delete_poly_button.grid(row=7, columnspan=2, padx=5, pady=(10, 30), sticky="we")

        self.select_all_button.grid(row=8, columnspan=2, padx=5, pady=10, sticky="we")
        self.deselect_all_button.grid(row=9, columnspan=2, padx=5, pady=(10, 30), sticky="we")

        self.threshold_label.grid(row=10, columnspan=2, padx=5, pady=10, sticky="we")
        self.threshold_scale.grid(row=11, columnspan=2, column=0, padx=5, pady=10, sticky="we")
        self.make_tight_button.grid(row=12, columnspan=2, column=0, padx=5, pady=10, sticky="we")
        self.auto_tight_poly_checkbutton.grid(row=13, columnspan=2, column=0, padx=5, pady=(10, 30), sticky="we")

        self.label_text_header.grid(row=14, columnspan=2, column=0, padx=5, pady=10, sticky="we")
        self.label_text.grid(row=15, columnspan=2, column=0, padx=5, pady=10, sticky="we")
        self.label_type_header.grid(row=16, columnspan=2, padx=5, pady=10, sticky="we")
        self.label_type.grid(row=17, columnspan=2, padx=5, pady=10, sticky="we")

        self.progress_bar.grid(row=19, columnspan=2, padx=5, pady=10, sticky="we")
        # Hide the progress_bar by default
        self.progress_bar.grid_remove()

        # Pack Frames
        self.left_frame.pack(side="left")
        self.top_frame.pack(side="bottom")
        self.bottom_frame.pack(side="left")

        # Configure Scrollbars
        self.hbar.pack(side="bottom", fill="x")
        self.hbar.configure(command=self.canvas.xview)
        self.vbar.pack(side="right", fill="y")
        self.vbar.configure(command=self.canvas.yview)

        # Configure Canvas
        max_w, max_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.configure(
            scrollregion=(0, 0, max_w - self.canvas.winfo_width(), max_h),
            yscrollcommand=self.vbar.set,
            xscrollcommand=self.hbar.set,
        )
        self.canvas.pack()
        self.hide_buttons()
        self.load_image_directory_button.configure(state="normal")

    def _validate_numeric_input(self, new_value: str) -> bool:
        """
        Validation function to allow only numeric input.
        """
        return new_value.isdigit()

    def hide_buttons(self):
        """
        Hide all buttons
        """
        self.load_image_directory_button.configure(state="disabled")
        self.jump_entry.configure(state="disabled")
        self.jump_button.configure(state="disabled")
        self.auto_annotate_button.configure(state="disabled")
        self.next_img_button.configure(state="disabled")
        self.save_image_button.configure(state="disabled")
        self.delete_poly_button.configure(state="disabled")
        self.deselect_all_button.configure(state="disabled")
        self.select_all_button.configure(state="disabled")
        self.draw_poly_button.configure(state="disabled")
        self.make_tight_button.configure(state="disabled")
        self.label_text.configure(state="disabled")
        self.label_type.configure(state="disabled")

    def show_buttons(self):
        """
        Show all buttons
        """
        self.jump_entry.configure(state="normal")
        self.jump_button.configure(state="normal")
        self.auto_annotate_button.configure(state="normal")
        self.next_img_button.configure(state="normal")
        self.save_image_button.configure(state="normal")
        self.delete_poly_button.configure(state="normal")
        self.deselect_all_button.configure(state="normal")
        self.select_all_button.configure(state="normal")
        self.draw_poly_button.configure(state="normal")
        self.make_tight_button.configure(state="normal")
        self.label_text.configure(state="normal")
        self.label_type.configure(state="normal")

    def select_all(self, event: tk.Event | None = None):
        """
        Select all polygons
        """
        for poly in self.img_cnv.polygons:  # type: ignore[union-attr]
            poly.select_polygon()

    def deselect_all(self, event: tk.Event | None = None):
        """
        Deselect all polygons
        """
        for poly in self.img_cnv.polygons:  # type: ignore[union-attr]
            poly.deselect_poly()

    def save_label(self, *args):
        """
        Save the label of the polygon in real-time.
        """
        if not self.img_cnv or not hasattr(self, "last_selected_polygon"):
            return

        last_selected_polygon = next(
            (poly for poly in self.img_cnv.polygons if poly.polygon_id == self.last_selected_polygon), None
        )
        if last_selected_polygon and last_selected_polygon.select_poly:
            with self.img_cnv.polygons_mutex:
                new_label = self.label_variable.get().strip()
                last_selected_polygon.text = new_label
            self.img_cnv.current_saved = False
            self.save_image_button.configure(state="normal")

    def save_type(self, *args):
        """
        Save the type of the polygon in real-time.
        """
        if not self.img_cnv or not hasattr(self, "last_selected_polygon"):
            return

        last_selected_polygon = next(
            (poly for poly in self.img_cnv.polygons if poly.polygon_id == self.last_selected_polygon), None
        )
        if last_selected_polygon and last_selected_polygon.select_poly:
            with self.img_cnv.polygons_mutex:
                new_type = self.type_variable.get().strip()
                last_selected_polygon.poly_type = new_type
            self.img_cnv.current_saved = False
            self.save_image_button.configure(state="normal")

    def load_new_img(self):
        """
        Load a new image
        """
        self.canvas.delete("all")
        self.save_image_button.configure(state="disabled")
        self.img_cnv = None
        path = os.path.join(self.image_dir, self.image_name)  # type: ignore[arg-type]
        self.img_cnv = ImageOnCanvas(self, self.canvas, path)
        logger.info(f"Loaded image: {path}")

        self.title(f"docTR-Labeler - {self.image_name} -> Progress: {self.curr_idx + 1}/{len(self.images_in_dir)}")  # type: ignore[operator]

        if len(self.img_cnv.polygons) > 0:
            self.auto_annotate_button.configure(state="disabled")
        else:
            self.auto_annotate_button.configure(state="normal")

    def auto_annotate(self):
        """
        Auto annotate the image
        """
        # Show the progress bar
        self.progress_bar.grid()
        self.progress_bar.start()

        # Background task to make tight boxes
        def _background_task():
            self.auto_annotate_button.configure(state="disabled")
            self.hide_buttons()
            self.img_cnv.auto_annotate()  # type: ignore[union-attr]

            # Stop the progress bar and hide it (must be done on the main thread)
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.show_buttons()
            self.auto_annotate_button.configure(state="disabled")

        # Start the background task in a separate thread
        threading.Thread(target=_background_task, daemon=True).start()
        self.img_cnv.current_saved = False  # type: ignore[union-attr]
        self.save_image_button.configure(state="normal")

    def load_directory(self):
        """
        Prompt the user to select a directory and load supported images.
        """

        def _get_supported_images(directory):
            """
            Helper method to filter supported images from a directory.
            """
            try:
                file_names = sorted(os.listdir(directory))
                return [name for name in file_names if name.split(".")[-1].lower() in self.supported_formats]
            except Exception as e:
                self.pop_up(f"Error reading the directory: {e}")
                return []

        try:
            if self.cli_usage:
                directory = filedialog.askdirectory()
            else:
                directory = self.image_dir  # type: ignore[assignment]

            if not directory:
                return

            # Collect supported images
            supported_images = _get_supported_images(directory)
            if not supported_images:
                self.pop_up("No supported images in the selected directory")
                return

            # Update instance attributes
            self.directory = directory
            self.image_dir = directory
            self.images_in_dir = supported_images
            self.curr_idx = None
            self.image_name = None

            # Show UI components and load the next image
            self.show_buttons()
            self.next_img()

        except Exception as e:
            self.pop_up(f"Error accessing the selected directory: {e}")

    def pop_up(self, text: str, save_msg: bool = False):  # pragma: no cover
        """
        Display a pop-up message with the given text.
        """
        top = tk.Toplevel(width=self.button_width * 4)
        top.title("docTR Labeler - Message")

        # Display the message text
        msg = tk.Label(top, text=text, font=("Arial", 14), anchor="w", justify="left")
        msg.pack(pady=10)

        # Create a frame for the buttons
        button_frame = tk.Frame(top)
        button_frame.pack()

        # Define the action for the Dismiss button
        def on_dismiss():
            if save_msg:
                top.destroy()
                self.load_new_img()
            else:
                top.destroy()

        def on_save():
            top.destroy()
            self.saver()
            self.load_new_img()

        # Define the 'Dismiss' button action
        dismiss_button = ttk.Button(button_frame, text="Dismiss", command=on_dismiss, width=self.button_width * 2)
        dismiss_button.pack(side=tk.LEFT, padx=5, pady=10)

        if save_msg:
            # Define the 'Save' button action
            save_button = ttk.Button(button_frame, text="Save", command=on_save, width=self.button_width * 2)
            save_button.pack(side=tk.LEFT, padx=5, pady=10)

    def jump_to_image(self):
        """
        Jump to a specific image by its index in the directory.
        """
        try:
            jump_idx = int(self.jump_entry.get())
            if jump_idx < 1 or jump_idx >= len(self.images_in_dir) + 1:
                self.pop_up("Invalid image index")
                return
            self.curr_idx = jump_idx - 2
            self.next_img()
        except ValueError:
            self.pop_up("Invalid image index")

    def next_img(self):
        """
        Load the next image in the directory.
        """
        if self.curr_idx is None:
            self.curr_idx = -1
        self.curr_idx = self.curr_idx + 1
        if self.curr_idx >= len(self.images_in_dir):
            self.pop_up(
                "Done with Images in this directory - "
                + "temporary saved labels will be merged now into the final json file"
            )
            self.curr_idx = self.curr_idx - 1
            # Final save
            self.img_cnv.final_save()  # type: ignore[union-attr]
            return
        if self.curr_idx > 0:
            self.prev_img_button.configure(state="normal")

        self.label_variable.set("")
        self.type_variable.set(self.type_options[0])

        self.image_name = self.images_in_dir[self.curr_idx]
        if self.img_cnv and not self.img_cnv.current_saved:
            self.pop_up("You have unsaved changes. Do you want to save them?", save_msg=True)
        else:
            self.load_new_img()

    def previous_img(self):
        """
        Load the previous image in the directory.
        """
        if self.curr_idx == 1:
            self.curr_idx = -1
            self.prev_img_button.configure(state="disabled")
        else:
            self.curr_idx = self.curr_idx - 2  # type: ignore[operator]
        self.next_img()

    def delete_selected(self, event: tk.Event | None = None):
        """
        Delete the selected polygons
        """
        # Collect the indices of polygons to delete
        indices_to_delete = [i for i, poly in enumerate(self.img_cnv.polygons) if poly.select_poly]  # type: ignore[union-attr]

        # Delete the selected polygons and their associated attributes
        for offset, idx in enumerate(indices_to_delete):
            adjusted_idx = idx - offset
            self.img_cnv.polygons[adjusted_idx].delete_self()  # type: ignore[union-attr]
            self.img_cnv.polygons.pop(adjusted_idx)  # type: ignore[union-attr]

        self.label_variable.set("")
        self.type_variable.set(self.type_options[0])

        # Check if all polygons are deleted
        if len(self.img_cnv.polygons) == 0:  # type: ignore[union-attr]
            self.auto_annotate_button.configure(state="normal")

        self.img_cnv.current_saved = False  # type: ignore[union-attr]
        self.save_image_button.configure(state="normal")

    def saver(self, event: tk.Event | None = None):
        """
        Save the annotations for the image
        """
        logger.info(f"Saving annotations for {self.image_name}")
        self.save_image_button.configure(state="disabled")
        saving_path = self.img_cnv.save_json()  # type: ignore[union-attr]
        logger.info(f"Annotations saved to {saving_path}")
        self.img_cnv.current_saved = True  # type: ignore[union-attr]

    def draw_poly_func(self, event: tk.Event | None = None):
        """
        Draw a polygon on the canvas
        """
        self.deselect_all()
        self.img_cnv.drawing_polygon = True  # type: ignore[union-attr]
        self.hide_buttons()
        self.drawing_obj = DrawPoly(self.bottom_frame, self.canvas, self.img_cnv, self.save_drawing)

    def save_drawing(self):
        """
        Save the drawing of the polygon
        """
        self.show_buttons()
        self.img_cnv.drawing_polygon = False  # type: ignore[union-attr]
        new_poly_pts = self.drawing_obj.pt_coords  # type: ignore[union-attr]
        # Remove temporary points from the canvas
        for pt in self.drawing_obj.points:  # type: ignore[union-attr]
            self.canvas.delete(pt)

        # Rescale polygon points if a scale factor exists
        if self.img_cnv.scale_factor is not None:  # type: ignore[union-attr]
            new_poly_pts = [[coord / self.img_cnv.scale_factor for coord in point] for point in new_poly_pts]  # type: ignore[union-attr]
        self.img_cnv.add_poly(new_poly_pts)  # type: ignore[union-attr]
        self.drawing_obj.delete_self()  # type: ignore[union-attr]
        self.drawing_obj = None

        # Re-enable drawing if "Keep Drawing" mode is enabled
        if self.keep_drawing.get():
            self.draw_poly_func()

        if self.auto_tight_poly.get():
            poly = self.img_cnv.polygons[-1]  # type: ignore[union-attr]
            for polyg in self.img_cnv.polygons:  # type: ignore[union-attr]
                polyg.select_poly = False
            poly.select_poly = True
            self.make_tight()
            poly.select_poly = False

            # Auto predict the label (only with make tight)
            self.img_cnv.auto_label(self.img_cnv.polygons[-1])  # type: ignore[union-attr]

        # Disable the auto annotate button if there are polygons
        self.auto_annotate_button.configure(state="disabled")
        # Enable the save button
        self.img_cnv.current_saved = False  # type: ignore[union-attr]
        self.save_image_button.configure(state="normal")

    def discard_drawing(self, event: tk.Event | None = None):
        """
        Discard the drawing of the polygon
        """
        self.show_buttons()
        self.img_cnv.drawing_polygon = False  # type: ignore[union-attr]
        self.drawing_obj.delete_self()  # type: ignore[union-attr]
        self.drawing_obj = None
        self.img_cnv.current_saved = False  # type: ignore[union-attr]
        self.save_image_button.configure(state="normal")

    def make_tight(self, event: tk.Event | None = None):
        """
        Make tight boxes around the selected polygons
        """
        num_selected = sum(poly.select_poly for poly in self.img_cnv.polygons)  # type: ignore[union-attr]
        logger.info(f"Agjust polygons for {num_selected} selected polygons")
        if num_selected > 1:
            # Show the progress bar
            self.progress_bar.grid()
            self.progress_bar.start()

            # Background task to make tight boxes
            def _background_task():
                self.hide_buttons()
                self.tight_box_obj = TightBox(self, self.img_cnv, self.threshold_scale.get())
                self.tight_box_obj.tight_box()

                # Stop the progress bar and hide it (must be done on the main thread)
                self.progress_bar.stop()
                self.progress_bar.grid_remove()
                self.show_buttons()
                self.auto_annotate_button.configure(state="disabled")

            # Start the background task in a separate thread
            background_thread = threading.Thread(target=_background_task, daemon=True)
            background_thread.start()

            # Periodically check if the thread is done
            def check_thread():  # pragma: no cover
                if not background_thread.is_alive():
                    self.deselect_all()  # Deselect all polygons after the thread finishes
                else:
                    self.after(100, check_thread)  # Check again after 100 ms

            self.after(100, check_thread)
        else:
            self.tight_box_obj = TightBox(self, self.img_cnv, self.threshold_scale.get())
            self.tight_box_obj.tight_box()
            self.deselect_all()

        self.save_image_button.configure(state="normal")

    def discard_tight(self, event: tk.Event | None = None):
        """
        Discard the changes made to the polygons by the tight_box method
        """
        try:
            self.tight_box_obj.discard_tight_box()  # type: ignore[union-attr]
            self.tight_box_obj = None
            self.img_cnv.current_saved = False  # type: ignore[union-attr]
            self.save_image_button.configure(state="normal")
        except AttributeError:  # pragma: no cover
            pass

    def start_gui(self):  # pragma: no cover
        sv_ttk.set_theme(darkdetect.theme())
        if self.image_folder:
            self.load_directory()
        self.mainloop()
