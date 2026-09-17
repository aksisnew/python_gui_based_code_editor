import queue
import threading
import tkinter as tk


class ContextMenuOptions:
    def __init__(self, root_window, action_callbacks=None):
        """
        options.py
        """
        self.root = root_window
        self.callbacks = action_callbacks or {}
        self.task_queue = queue.Queue()
        
        # Build the context menu popup widget
        self.menu = tk.Menu(self.root, tearoff=0)
        self._build_menu()
        
        # Start background listener for context requests
        self._process_queue()

    def _build_menu(self):
        """Constructs context menu items."""
        self.menu.add_command(label="Cut", command=lambda: self._trigger("cut"))
        self.menu.add_command(label="Copy", command=lambda: self._trigger("copy"))
        self.menu.add_command(label="Paste", command=lambda: self._trigger("paste"))
        self.menu.add_separator()
        self.menu.add_command(label="Select All", command=lambda: self._trigger("select_all"))
        self.menu.add_separator()
        self.menu.add_command(label="Format Code", command=lambda: self._trigger("format"))

    def attach_to_widget(self, widget):
        """Binds right-click event to a target widget (supports Windows, Linux, and macOS)."""
        widget.bind("<Button-3>", self._on_right_click)  # Windows / Linux
        widget.bind("<Button-2>", self._on_right_click)  # macOS

    def _on_right_click(self, event):
        """Offloads context checking to a thread before displaying the popup."""
        threading.Thread(
            target=self._worker_handle_context,
            args=(event.x_root, event.y_root, event.widget),
            daemon=True
        ).start()

    def _worker_handle_context(self, x, y, widget):
        """Background Worker: Determines active context states safely."""
        has_selection = False
        try:
            if isinstance(widget, tk.Text) and widget.tag_ranges(tk.SEL):
                has_selection = True
        except tk.TclError:
            pass

        # Send display payload to queue
        self.task_queue.put(("show_menu", {
            "x": x,
            "y": y,
            "has_selection": has_selection
        }))

    def _process_queue(self):
        """Processes menu displays on the main Tkinter UI thread."""
        try:
            while True:
                action, payload = self.task_queue.get_nowait()
                if action == "show_menu":
                    # Dynamically enable/disable Cut/Copy based on active selection
                    state = tk.NORMAL if payload["has_selection"] else tk.DISABLED
                    self.menu.entryconfig("Cut", state=state)
                    self.menu.entryconfig("Copy", state=state)
                    
                    self.menu.tk_popup(payload["x"], payload["y"])
        except queue.Empty:
            pass
        finally:
            self.menu.grab_release()

        self.root.after(50, self._process_queue)

    def _trigger(self, action_name):
        """Executes the mapped callback for the selected context action."""
        if action_name in self.callbacks and callable(self.callbacks[action_name]):
            self.callbacks[action_name]()
