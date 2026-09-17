import queue
import threading
import tkinter as tk
from tkinter import ttk


class BottomBar(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """
        Initializes the BottomBar component with multi-threaded event processing
        to prevent status updates from blocking the main UI thread.
        """
        super().__init__(parent, *args, **kwargs)
        
        # Thread-safe queue for UI updates
        self.update_queue = queue.Queue()
        
        # UI Elements
        self.status_label = ttk.Label(self, text="Ready", anchor="w")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stats_label = ttk.Label(
            self, 
            text="Ln 1, Col 0 | Chars: 0 | Sel: 0 chars (0 lines)", 
            anchor="e"
        )
        self.stats_label.pack(side=tk.RIGHT, padx=5)
        
        # Start queue listener loop on the main Tkinter thread
        self._process_queue_events()

    def update_stats_async(self, stats):
        """
        Public API: Receives stats dict from editor.py. Spawns a background thread 
        to process calculations and posts the result to the queue.
        """
        threading.Thread(target=self._worker_process_stats, args=(stats,), daemon=True).start()

    def _worker_process_stats(self, stats):
        """
        Background Thread Worker: Offloads formatting and string construction 
        away from the main UI thread.
        """
        line = stats.get("line", 1)
        col = stats.get("column", 0)
        total_chars = stats.get("total_chars", 0)
        sel_chars = stats.get("selected_chars", 0)
        sel_lines = stats.get("selected_lines", 0)
        
        formatted_text = f"Ln {line}, Col {col} | Chars: {total_chars} | Sel: {sel_chars} chars ({sel_lines} lines)"
        
        # Put the processed state into the thread-safe queue
        self.update_queue.put(("stats", formatted_text))

    def set_status_async(self, message):
        """
        Public API: Safely sets a status message (e.g., 'File Saved') from any thread.
        """
        threading.Thread(target=lambda: self.update_queue.put(("status", message)), daemon=True).start()

    def _process_queue_events(self):
        """
        Main Loop Listener: Periodically checks the queue and applies UI updates on the main thread.
        """
        try:
            while True:
                msg_type, data = self.update_queue.get_nowait()
                if msg_type == "stats":
                    self.stats_label.config(text=data)
                elif msg_type == "status":
                    self.status_label.config(text=data)
        except queue.Empty:
            pass
        
        # Check queue every 50ms
        self.after(50, self._process_queue_events)
