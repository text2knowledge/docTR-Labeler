import time
import unittest

import tkinter as tk

from labeler.custom_widgets.searchable_combobox import SearchableComboBox


class TestSearchableComboBox(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.values = ["words", "header", "footer"]
        self.combo = SearchableComboBox(self.root, self.values)
        self.combo.pack()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_initialization(self):
        self.assertEqual(self.combo.values, self.values)
        self.assertEqual(self.combo.entry.get(), "")
        self.assertFalse(self.combo.popup.winfo_viewable())

    def test_filter_on_keyrelease(self):
        self.combo.entry.insert(0, "wo")
        event = tk.Event()
        event.keysym = "r"
        self.combo._on_keyrelease(event)

        self.assertEqual(self.combo.filtered_values, ["words"])
        self.assertTrue(self.combo.popup.winfo_viewable())

    def test_on_keyrelease_ignored_keys(self):
        self.combo.entry.insert(0, "words")
        event = tk.Event()
        event.keysym = "Up"
        initial = self.combo.filtered_values
        self.combo._on_keyrelease(event)
        self.assertEqual(self.combo.filtered_values, initial)

    def test_keyrelease_no_results(self):
        self.combo.entry.insert(0, "XYZ")
        event = tk.Event()
        event.keysym = "Z"
        self.combo._on_keyrelease(event)
        self.assertFalse(self.combo.popup.winfo_viewable())

    def test_toggle_dropdown(self):
        self.combo._toggle_dropdown()
        self.root.update()
        self.assertTrue(self.combo.popup.winfo_viewable())

        self.combo._toggle_dropdown()
        self.root.update()
        self.assertFalse(self.combo.popup.winfo_viewable())

    def test_select_item(self):
        self.combo._select_item("footer")
        self.assertEqual(self.combo.entry.get(), "footer")
        self.assertFalse(self.combo.popup.winfo_viewable())

    def test_arrow_navigation(self):
        self.combo._toggle_dropdown()
        event = tk.Event()
        event.keysym = "Down"
        self.combo._on_arrow_navigation(event)

        selection = self.combo.listbox.curselection()
        self.assertEqual(selection[0], 0)
        self.assertEqual(self.combo.listbox.get(0), "words")

    def test_arrow_navigation_up(self):
        self.combo._toggle_dropdown()
        self.combo._update_selection(1)
        event = tk.Event()
        event.keysym = "Up"
        self.combo._on_arrow_navigation(event)
        self.assertEqual(self.combo.listbox.curselection()[0], 0)

    def test_arrow_navigation_opens_popup(self):
        self.combo.popup.withdraw()
        event = tk.Event()
        event.keysym = "Down"
        self.assertEqual(self.combo._on_arrow_navigation(event), "break")
        self.assertTrue(self.combo.popup.winfo_viewable())

    def test_enter_select(self):
        self.combo._toggle_dropdown()
        self.combo._update_selection(1)
        self.assertEqual(self.combo._on_enter_select(tk.Event()), "break")
        self.assertEqual(self.combo.entry.get(), "header")

        self.combo.popup.withdraw()
        self.assertIsNone(self.combo._on_enter_select(tk.Event()))
        
        self.combo._toggle_dropdown()
        self.combo.listbox.selection_clear(0, tk.END)
        self.assertIsNone(self.combo._on_enter_select(tk.Event()))

    def test_on_listbox_click(self):
        self.combo._toggle_dropdown()
        self.combo.listbox.selection_set(2)
        self.combo._on_listbox_click(None)
        self.assertEqual(self.combo.entry.get(), "footer")

    def test_popup_position(self):
        self.combo._show_popup()
        self.root.update()
        x = int(self.combo.popup.winfo_geometry().split("+")[1])
        self.assertEqual(x, self.combo.entry_frame.winfo_rootx())

    def test_focus_out_logic(self):
        self.combo._toggle_dropdown()
        self.assertTrue(self.combo.popup.winfo_viewable())
        other = tk.Entry(self.root)
        other.pack()
        other.focus_set()
        self.root.update()
        for _ in range(10):
            self.root.update()
            time.sleep(0.05)
            if not self.combo.popup.winfo_viewable():
                break
        self.combo._check_focus()
        self.root.update()
        self.assertFalse(self.combo.popup.winfo_viewable())
