import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog


class FileOpener:
    def __init__(self, root_window, open_callback=None):
        """
       along with files.py
        """
        self.root = root_window
        self.open_callback = open_callback

  

    def open_file_dialog_async(self):
        """Opens file selection dialog and reads selected file off-thread."""
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="Open File",
            filetypes=[("All Files", "*.*"), ("Python Files", "*.py"), ("Text Files", "*.txt")]
        )
        if file_path:
            self.load_file_content_async(file_path)

    def open_folder_dialog_async(self):
        """Opens directory selection dialog and scans workspace off-thread."""
        folder_path = filedialog.askdirectory(
            parent=self.root,
            title="Open Folder / Workspace"
        )
        if folder_path:
            threading.Thread(
                target=self._worker_scan_folder, 
                args=(folder_path,), 
                daemon=True
            ).start()

    def load_file_content_async(self, file_path):
        """Reads file contents asynchronously in a background thread."""
        threading.Thread(
            target=self._worker_read_file, 
            args=(file_path,), 
            daemon=True
        ).start()

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_read_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._dispatch_event("file_loaded", {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "content": content
            })
        except Exception as e:
            self._dispatch_event("error", {
                "action": "open_file",
                "file_path": file_path,
                "message": f"Failed to read file: {str(e)}"
            })

    def _worker_scan_folder(self, folder_path):
        try:
            structure = []
            for root, dirs, files in os.walk(folder_path):
                structure.append({
                    "root": root,
                    "dirs": dirs,
                    "files": files
                })
                break  # Fetch immediate top-level directory structure first for quick load
                
            self._dispatch_event("folder_loaded", {
                "folder_path": folder_path,
                "folder_name": os.path.basename(folder_path),
                "structure": structure
            })
        except Exception as e:
            self._dispatch_event("error", {
                "action": "open_folder",
                "folder_path": folder_path,
                "message": f"Failed to scan folder: {str(e)}"
            })

    def _dispatch_event(self, event_type, payload):
        """Safely relays worker results to the UI thread via callback."""
        if self.open_callback:
            payload["event"] = event_type
            self.root.after(0, lambda: self.open_callback(payload))
