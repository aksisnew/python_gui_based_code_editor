import tkinter as tk


class ActionBarMenu:
    def __init__(self, root_window, callbacks=None):
        """
       action bar
        """
        self.root = root_window
        self.callbacks = callbacks or {}
        
        # Create Main Menu Bar
        self.menu_bar = tk.Menu(self.root)
        
        # Build Menus
        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_tools_menu()
        
        # Attach to root window
        self.root.config(menu=self.menu_bar)

    def _build_file_menu(self):
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New File", command=lambda: self._trigger("new_file"))
        file_menu.add_command(label="Open File...", command=lambda: self._trigger("open_file"))
        file_menu.add_command(label="Open Folder...", command=lambda: self._trigger("open_folder"))
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=lambda: self._trigger("save"))
        file_menu.add_command(label="Save As...", command=lambda: self._trigger("save_as"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=lambda: self._trigger("exit"))
        
        self.menu_bar.add_cascade(label="File", menu=file_menu)

    def _build_edit_menu(self):
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=lambda: self._trigger("undo"))
        edit_menu.add_command(label="Redo", command=lambda: self._trigger("redo"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self._trigger("cut"))
        edit_menu.add_command(label="Copy", command=lambda: self._trigger("copy"))
        edit_menu.add_command(label="Paste", command=lambda: self._trigger("paste"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=lambda: self._trigger("select_all"))
        
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

    def _build_view_menu(self):
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Toggle Sidebar", command=lambda: self._trigger("toggle_sidebar"))
        view_menu.add_command(label="Toggle Bottom Bar", command=lambda: self._trigger("toggle_bottombar"))
        view_menu.add_command(label="Toggle Options Panel", command=lambda: self._trigger("toggle_options"))
        
        self.menu_bar.add_cascade(label="View", menu=view_menu)

    def _build_tools_menu(self):
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Find / Search", command=lambda: self._trigger("find"))
        tools_menu.add_command(label="Run Addons", command=lambda: self._trigger("run_addons"))
        
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)

    def _trigger(self, action_name):
        """Safely invokes registered callback actions."""
        if action_name in self.callbacks and callable(self.callbacks[action_name]):
            self.callbacks[action_name]()
