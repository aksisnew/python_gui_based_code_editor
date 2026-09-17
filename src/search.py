
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk


class SearchEngine:
    def __init__(self, root_window, get_editor_text_fn=None, replace_text_fn=None):
        """
      search.py
        """
        self.root = root_window
        self.get_editor_text_fn = get_editor_text_fn
        self.replace_text_fn = replace_text_fn
        self.task_queue = queue.Queue()
        
        self.dialog = None
        self._process_queue()

    def show_find_dialog(self):
        """Displays the non-blocking Find & Replace popup."""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            return

        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Find and Replace")
        self.dialog.geometry("360x160")
        self.dialog.resizable(False, False)

        ttk.Label(self.dialog, text="Find:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.find_entry = ttk.Entry(self.dialog, width=25)
        self.find_entry.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(self.dialog, text="Replace:").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.replace_entry = ttk.Entry(self.dialog, width=25)
        self.replace_entry.grid(row=1, column=1, padx=8, pady=8)

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Find All", command=self.find_all_async).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Replace All", command=self.replace_all_async).pack(side=tk.LEFT, padx=4)

        self.status_label = ttk.Label(self.dialog, text="")
        self.status_label.grid(row=3, column=0, columnspan=2)

    def find_all_async(self):
        """Triggers asynchronous search query."""
        target_str = self.find_entry.get()
        if not target_str or not self.get_editor_text_fn:
            return
            
        code_text = self.get_editor_text_fn()
        threading.Thread(
            target=self._worker_find,
            args=(target_str, code_text),
            daemon=True
        ).start()

    def replace_all_async(self):
        """Triggers asynchronous find and replace substitution."""
        target_str = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not target_str or not self.get_editor_text_fn:
            return

        code_text = self.get_editor_text_fn()
        threading.Thread(
            target=self._worker_replace,
            args=(target_str, replacement, code_text),
            daemon=True
        ).start()

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_find(self, target_str, text):
        matches = [m.start() for m in re.finditer(re.escape(target_str), text)]
        self.task_queue.put(("find_result", {
            "count": len(matches),
            "target": target_str
        }))

    def _worker_replace(self, target_str, replacement, text):
        updated_text, count = re.subn(re.escape(target_str), replacement, text)
        self.task_queue.put(("replace_result", {
            "updated_text": updated_text,
            "count": count
        }))

   

    def _process_queue(self):
        try:
            while True:
                action, payload = self.task_queue.get_nowait()
                if action == "find_result":
                    msg = f"Found {payload['count']} occurrence(s) of '{payload['target']}'"
                    if self.status_label and self.status_label.winfo_exists():
                        self.status_label.config(text=msg)
                elif action == "replace_result":
                    if self.replace_text_fn:
                        self.replace_text_fn(payload["updated_text"])
                    msg = f"Replaced {payload['count']} occurrence(s)"
                    if self.status_label and self.status_label.winfo_exists():
                        self.status_label.config(text=msg)
        except queue.Empty:
            pass

        self.root.after(50, self._process_queue)
