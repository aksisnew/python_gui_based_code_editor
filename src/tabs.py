import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk


class TabManager(ttk.Notebook):
    def __init__(self, parent, create_editor_callback, *args, **kwargs):
        """
        tabs.py
        """
        super().__init__(parent, *args, **kwargs)
        self.create_editor_callback = create_editor_callback
        
        # Dictionary mapping tab_id -> {"editor": EditorEngine, "file_path": str, "frame": Frame}
        self.tabs_data = {}
        self.task_queue = queue.Queue()
        
        # Enable middle-click to close tab
        self.bind("<Button-2>", self._on_middle_click_close)
        
        # Start queue loop
        self._process_queue()

    def add_tab_async(self, file_path=None, title="Untitled", content=""):
        """Public API: Opens a new editor tab asynchronously."""
        threading.Thread(
            target=self._worker_add_tab,
            args=(file_path, title, content),
            daemon=True
        ).start()

    def close_active_tab_async(self):
        """Public API: Closes current active tab safely."""
        current_tab_id = self.select()
        if current_tab_id:
            self.close_tab_async(current_tab_id)

    def close_tab_async(self, tab_id):
        """Closes a specific tab off-thread."""
        threading.Thread(
            target=self._worker_close_tab,
            args=(tab_id,),
            daemon=True
        ).start()

    def get_active_editor(self):
        """Returns the EditorEngine instance associated with the currently selected tab."""
        current_tab_id = self.select()
        if current_tab_id in self.tabs_data:
            return self.tabs_data[current_tab_id]["editor"]
        return None

    def get_active_file_path(self):
        """Returns the file path of the currently selected tab."""
        current_tab_id = self.select()
        if current_tab_id in self.tabs_data:
            return self.tabs_data[current_tab_id]["file_path"]
        return None

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_add_tab(self, file_path, title, content):
        # Post request to UI thread to create tab widget elements
        self.task_queue.put(("create_tab", {
            "file_path": file_path,
            "title": title,
            "content": content
        }))

    def _worker_close_tab(self, tab_id):
        # Notify queue to remove tab from UI safely
        self.task_queue.put(("remove_tab", {"tab_id": tab_id}))

    def _process_queue(self):
        """Processes tab creation and deletion events on the Tkinter main thread."""
        try:
            while True:
                action, payload = self.task_queue.get_nowait()
                if action == "create_tab":
                    self._create_tab_ui(payload["file_path"], payload["title"], payload["content"])
                elif action == "remove_tab":
                    self._remove_tab_ui(payload["tab_id"])
        except queue.Empty:
            pass
        
        self.after(50, self._process_queue)

    def _create_tab_ui(self, file_path, title, content):
        tab_frame = ttk.Frame(self)
        
        # Instantiate editor engine using the passed callback
        editor = self.create_editor_callback(tab_frame)
        if content:
            editor.set_text(content)
            
        self.add(tab_frame, text=title)
        tab_id = self.tabs()[-1]
        
        self.tabs_data[tab_id] = {
            "editor": editor,
            "file_path": file_path,
            "frame": tab_frame
        }
        self.select(tab_frame)

    def _remove_tab_ui(self, tab_id):
        if tab_id in self.tabs_data:
            self.forget(tab_id)
            del self.tabs_data[tab_id]

    def _on_middle_click_close(self, event):
        """Allows middle clicking on a tab header to close it."""
        try:
            index = self.index(f"@{event.x},{event.y}")
            tab_id = self.tabs()[index]
            self.close_tab_async(tab_id)
        except tk.TclError:
            pass
