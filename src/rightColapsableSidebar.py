import os
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk


class RightCollapsibleSidebar(ttk.Frame):
    def __init__(self, parent, on_file_select_callback=None, *args, **kwargs):
        """
        Collapsible right sidebar 
        """
        super().__init__(parent, *args, **kwargs)
        self.on_file_select_callback = on_file_select_callback
        self.task_queue = queue.Queue()
        self.is_collapsed = False

        # Toggle Button Header
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.toggle_btn = ttk.Button(self.header_frame, text="▶ Sidebar", command=self.toggle)
        self.toggle_btn.pack(side=tk.RIGHT, fill=tk.X)

        # Main Sidebar Content Container
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Tabbed Layout for File Explorer and Symbol Outline
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 1. File Explorer Tab
        self.explorer_frame = ttk.Frame(self.notebook)
        self.file_tree = ttk.Treeview(self.explorer_frame, show="tree")
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.bind("<Double-1>", self._on_tree_double_click)
        self.notebook.add(self.explorer_frame, text="Explorer")

        # 2. Outline / Symbols Tab
        self.outline_frame = ttk.Frame(self.notebook)
        self.symbol_list = tk.Listbox(self.outline_frame)
        self.symbol_list.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(self.outline_frame, text="Symbols")

        # Start queue listener
        self._process_queue()

    def toggle(self):
        """Toggles sidebar visibility."""
        if self.is_collapsed:
            self.content_frame.pack(fill=tk.BOTH, expand=True)
            self.toggle_btn.config(text="▶ Sidebar")
            self.is_collapsed = False
        else:
            self.content_frame.pack_forget()
            self.toggle_btn.config(text="◀ Sidebar")
            self.is_collapsed = True

    def populate_explorer_async(self, folder_path):
        """Public API: Populates workspace file tree asynchronously."""
        threading.Thread(
            target=self._worker_scan_directory,
            args=(folder_path,),
            daemon=True
        ).start()

    def parse_symbols_async(self, code_text):
        """Public API: Extracts functions and classes from current editor content asynchronously."""
        threading.Thread(
            target=self._worker_parse_symbols,
            args=(code_text,),
            daemon=True
        ).start()

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_scan_directory(self, folder_path):
        """Custom directory listing to avoid generic walk implementations."""
        try:
            entries = os.listdir(folder_path)
            directories = [e for e in entries if os.path.isdir(os.path.join(folder_path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(folder_path, e))]
        except Exception:
            directories, files = [], []

        self.task_queue.put(("update_explorer", {
            "folder_path": folder_path,
            "dirs": directories,
            "files": files
        }))

    def _worker_parse_symbols(self, code_text):
        """Parses python function and class signatures line by line."""
        symbols = []
        for line in code_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("def "):
                name = line_str.split("(")[0].replace("def ", "").strip()
                symbols.append(f"def: {name}")
            elif line_str.startswith("class "):
                name = line_str.split("(")[0].split(":")[0].replace("class ", "").strip()
                symbols.append(f"class: {name}")

        self.task_queue.put(("update_symbols", symbols))

    # ================================
    # Queue Dispatcher & UI Event Handlers
    # ================================

    def _process_queue(self):
        try:
            while True:
                action, payload = self.task_queue.get_nowait()
                if action == "update_explorer":
                    self._update_explorer_ui(payload["folder_path"], payload["dirs"], payload["files"])
                elif action == "update_symbols":
                    self._update_symbols_ui(payload)
        except queue.Empty:
            pass
            
        self.after(50, self._process_queue)

    def _update_explorer_ui(self, folder_path, dirs, files):
        self.file_tree.delete(*self.file_tree.get_children())
        root_node = self.file_tree.insert("", "end", text=os.path.basename(folder_path), open=True)
        
        for d in dirs:
            self.file_tree.insert(root_node, "end", text=f"📁 {d}", values=[os.path.join(folder_path, d)])
        for f in files:
            self.file_tree.insert(root_node, "end", text=f"📄 {f}", values=[os.path.join(folder_path, f)])

    def _update_symbols_ui(self, symbols):
        self.symbol_list.delete(0, tk.END)
        for sym in symbols:
            self.symbol_list.insert(tk.END, sym)

    def _on_tree_double_click(self, event):
        item = self.file_tree.selection()
        if item:
            values = self.file_tree.item(item[0], "values")
            if values and self.on_file_select_callback:
                file_path = values[0]
                if os.path.isfile(file_path):
                    self.on_file_select_callback(file_path)
