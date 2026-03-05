# Copyright (C) 2024-2026, Felix Dittrich | Ian List | Devarshi Aggarwal.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import tkinter as tk
from tkinter import ttk


class SearchableComboBox(ttk.Frame):
    """
    A custom Tkinter widget that combines an Entry field with a searchable dropdown list.

    This widget allows users to type into an entry field to filter a list of values
    displayed in a popup Toplevel window. It supports keyboard navigation (arrows, enter)
    and mouse interaction.
    """

    def __init__(self, parent, values, *args, **kwargs):
        """
        Initialize the SearchableComboBox.

        Args:
            parent: The parent widget.
            values (list): A list of strings to be displayed in the dropdown.
            *args: Variable length argument list passed to the tk.Frame.
            **kwargs: Arbitrary keyword arguments passed to the tk.Frame.
        """
        super().__init__(parent, *args, **kwargs)

        self.values = values
        self.filtered_values = values
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.pack(fill="x", expand=True)
        self.entry = ttk.Entry(self.entry_frame)
        self.entry.pack(side="left", fill="x", expand=True)
        self.drop_btn = ttk.Label(self.entry_frame, text="\u25bc", cursor="hand2") # unicode arrow down
        self.drop_btn.pack(side="right", fill="y", padx=(0, 5))
        self.drop_btn.bind("<Button-1>", lambda e: self._toggle_dropdown())

        # Dropdown popup setup
        self.popup = tk.Toplevel(self)
        self.popup.withdraw()
        self.popup.overrideredirect(True)
        self.listbox = tk.Listbox(self.popup, bd=1, highlightthickness=0, relief="solid")
        self.listbox.pack(fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(self.listbox, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Event bindings
        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<Down>", self._on_arrow_navigation)
        self.entry.bind("<Up>", self._on_arrow_navigation)
        self.entry.bind("<Return>", self._on_enter_select)
        self.entry.bind("<Escape>", lambda e: self.popup.withdraw())
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_click)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.listbox.bind("<FocusOut>", self._on_focus_out)

    def _on_keyrelease(self, event):
        """
        Handle key release events in the entry field for filtering.

        Args:
            event: The Tkinter event object.
        """
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return

        search_term = self.entry.get().lower()
        self.filtered_values = [item for item in self.values if search_term in item.lower()]

        if self.filtered_values:
            self._update_listbox(self.filtered_values)
            self._show_popup()
        else:
            self.popup.withdraw()

    def _on_arrow_navigation(self, event):
        """
        Handle arrow key navigation within the dropdown list.

        Args:
            event: The Tkinter event object containing the key symbol.

        Returns:
            str: "break" to prevent default Tkinter behavior.
        """
        if not self.popup.winfo_viewable():
            self._update_listbox(self.values)
            self._show_popup()
            return "break"

        current_selection = self.listbox.curselection()

        if event.keysym == "Down":
            next_index = (current_selection[0] + 1) if current_selection else 0
            if next_index < self.listbox.size():
                self._update_selection(next_index)

        elif event.keysym == "Up":
            prev_index = (current_selection[0] - 1) if current_selection else self.listbox.size() - 1
            if prev_index >= 0:
                self._update_selection(prev_index)

        return "break"

    def _update_selection(self, index):
        """
        Highlight and scroll to a specific index in the listbox.

        Args:
            index (int): The index of the item to select.
        """
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

    def _on_enter_select(self, event):
        """
        Select the currently highlighted listbox item when Enter is pressed.

        Args:
            event: The Tkinter event object.
        """
        if self.popup.winfo_viewable():
            selection = self.listbox.curselection()
            if selection:
                self._select_item(self.listbox.get(selection[0]))
                return "break"

    def _on_listbox_click(self, event):
        """
        Handle mouse click selection in the listbox.

        Args:
            event: The Tkinter event object.
        """
        if self.listbox.curselection():
            self._select_item(self.listbox.get(self.listbox.curselection()[0]))

    def _select_item(self, value):
        """
        Update the entry field with the selected value and close the popup.

        Args:
            value (str): The text value to set in the entry.
        """
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.popup.withdraw()
        self.entry.focus_set()

    def _toggle_dropdown(self):
        """Toggle the visibility of the dropdown popup."""
        if self.popup.winfo_viewable():
            self.popup.withdraw()
        else:
            self._update_listbox(self.values)
            self._show_popup()
            self.entry.focus_set()

    def _update_listbox(self, data):
        """
        Clear and refill the listbox with new data.

        Args:
            data (list): List of strings to populate the listbox.
        """
        self.listbox.delete(0, tk.END)
        for item in data:
            self.listbox.insert(tk.END, item)

    def _show_popup(self):
        """
        Calculate position and display the dropdown popup relative to the entry frame.
        """
        self.update_idletasks()
        x = self.entry_frame.winfo_rootx()
        y = self.entry_frame.winfo_rooty() + self.entry_frame.winfo_height()
        width = self.entry_frame.winfo_width()
        self.popup.geometry(f"{width}x150+{x}+{y}")
        self.popup.deiconify()
        self.popup.lift()

    def _on_focus_out(self, event):
        """
        Trigger a delayed check to hide the popup when focus is lost.

        Args:
            event: The Tkinter event object.
        """
        self.after(200, self._check_focus)

    def _check_focus(self):
        """
        Hide the popup if the focus has moved outside the widget's components.
        """
        focused = self.focus_get()
        if focused not in (self.entry, self.listbox, self.drop_btn):
            self.popup.withdraw()
