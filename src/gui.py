import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from actionBarMenu import ActionBarMenu
from bottombar import BottomBar
from editor import EditorEngine
from files import FileManager
from open import FileOpener
from options import ContextMenuOptions
from rightColapsableSidebar import RightCollapsibleSidebar
from search import SearchEngine
from tabs import TabManager
from Addons import AddonManager


class MainGUI(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.root = root
        self.root.title("Custom Multi-Threaded Text Editor")
        self.root.geometry("1024x768")

        self.pack(fill=tk.BOTH, expand=True)

        # 1. Initialize Thread-safe Helpers & Managers
        self.file_manager = FileManager(ui_callback=self._handle_file_manager_events)
        self.file_opener = FileOpener(self.root, open_callback=self._handle_file_opener_events)

        # 2. Build Layout Containers
        self._build_layout()

        # 3. Connect Component Engines
        self.tabs = TabManager(self.paned_window, create_editor_callback=self._create_editor_instance)
        self.paned_window.add(self.tabs, weight=3)

        self.sidebar = RightCollapsibleSidebar(self.paned_window, on_file_select_callback=self.file_opener.load_file_content_async)
        self.paned_window.add(self.sidebar, weight=1)

        self.bottom_bar = BottomBar(self)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 4. Attach Menus & Interactive Dialogs
        self.context_menu = ContextMenuOptions(self.root, action_callbacks={
            "cut": lambda: self.root.focus_get().event_generate("<<Cut>>") if self.root.focus_get() else None,
            "copy": lambda: self.root.focus_get().event_generate("<<Copy>>") if self.root.focus_get() else None,
            "paste": lambda: self.root.focus_get().event_generate("<<Paste>>") if self.root.focus_get() else None,
            "select_all": lambda: self.root.focus_get().event_generate("<<SelectAll>>") if self.root.focus_get() else None,
        })

        self.search_engine = SearchEngine(
            self.root,
            get_editor_text_fn=self._get_active_editor_text,
            replace_text_fn=self._set_active_editor_text
        )

        self.addon_manager = AddonManager(
            self.root,
            get_editor_text_fn=self._get_active_editor_text,
            set_editor_text_fn=self._set_active_editor_text
        )
        self.addon_manager.discover_addons_async()

        self.action_bar = ActionBarMenu(self.root, callbacks={
            "new_file": lambda: self.tabs.add_tab_async(title="Untitled"),
            "open_file": self.file_opener.open_file_dialog_async,
            "open_folder": self.file_opener.open_folder_dialog_async,
            "save": self._save_current_file,
            "save_as": self._save_as_current_file,
            "exit": self.root.quit,
            "undo": lambda: self._trigger_editor_event("<<Undo>>"),
            "redo": lambda: self._trigger_editor_event("<<Redo>>"),
            "cut": lambda: self._trigger_editor_event("<<Cut>>"),
            "copy": lambda: self._trigger_editor_event("<<Copy>>"),
            "paste": lambda: self._trigger_editor_event("<<Paste>>"),
            "select_all": lambda: self._trigger_editor_event("<<SelectAll>>"),
            "toggle_sidebar": self.sidebar.toggle,
            "find": self.search_engine.show_find_dialog,
            "run_addons": self.addon_manager.show_addons_dialog,
        })

        # Open initial blank tab
        self.tabs.add_tab_async(title="Untitled")

    def _build_layout(self):
        """Constructs split-pane layout."""
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

    def _create_editor_instance(self, parent_frame):
        """Factory method to inject into TabManager."""
        editor = EditorEngine(parent_frame, bottom_bar_callback=self.bottom_bar.update_stats_async)
        self.context_menu.attach_to_widget(editor.text_widget)
        return editor

    def _get_active_editor_text(self):
        editor = self.tabs.get_active_editor()
        return editor.get_text() if editor else ""

    def _set_active_editor_text(self, text):
        editor = self.tabs.get_active_editor()
        if editor:
            editor.set_text(text)

    def _trigger_editor_event(self, event_name):
        editor = self.tabs.get_active_editor()
        if editor:
            editor.text_widget.event_generate(event_name)

    def _save_current_file(self):
        editor = self.tabs.get_active_editor()
        file_path = self.tabs.get_active_file_path()
        if editor:
            content = editor.get_text()
            if file_path:
                self.file_manager.save_file_async(file_path, content)
            else:
                self._save_as_current_file()

    def _save_as_current_file(self):
        editor = self.tabs.get_active_editor()
        if editor:
            file_path = filedialog.asksaveasfilename(parent=self.root, title="Save As")
            if file_path:
                content = editor.get_text()
                self.file_manager.save_file_async(file_path, content, overwrite=True)

    def _handle_file_opener_events(self, payload):
        event = payload.get("event")
        if event == "file_loaded":
            self.tabs.add_tab_async(
                file_path=payload["file_path"],
                title=payload["file_name"],
                content=payload["content"]
            )
            self.bottom_bar.set_status_async(f"Loaded: {payload['file_name']}")
        elif event == "folder_loaded":
            self.sidebar.populate_explorer_async(payload["folder_path"])
            self.bottom_bar.set_status_async(f"Opened Folder: {payload['folder_name']}")
        elif event == "error":
            messagebox.showerror("File Error", payload.get("message", "An error occurred."))

    def _handle_file_manager_events(self, payload):
        event = payload.get("event")
        if event == "save_success":
            self.bottom_bar.set_status_async(payload["message"])
        elif event == "conflict":
            if messagebox.askyesno("File Conflict", payload["message"]):
                content = self._get_active_editor_text()
                self.file_manager.save_file_async(payload["file_path"], content, overwrite=True)
        elif event == "error":
            messagebox.showerror("Disk Error", payload.get("message", "Failed operation."))
