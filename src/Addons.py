import importlib.util
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk


class AddonManager:
    def __init__(self, root_window, addons_dir="addons", get_editor_text_fn=None, set_editor_text_fn=None):
        """
        addons.py
        """
        self.root = root_window
        self.addons_dir = addons_dir
        self.get_editor_text_fn = get_editor_text_fn
        self.set_editor_text_fn = set_editor_text_fn
        
        self.task_queue = queue.Queue()
        self.addons = {}
        
        # Start queue event loop
        self._process_queue()

    def discover_addons_async(self):
        """Discovers valid python addon scripts in the background."""
        threading.Thread(target=self._worker_discover_addons, daemon=True).start()

    def run_addon_async(self, addon_name):
        """Executes selected addon script off the main thread."""
        if addon_name not in self.addons:
            return
            
        script_path = self.addons[addon_name]
        current_text = self.get_editor_text_fn() if self.get_editor_text_fn else ""
        
        threading.Thread(
            target=self._worker_execute_addon,
            args=(addon_name, script_path, current_text),
            daemon=True
        ).start()

    def show_addons_dialog(self):
        """Displays popup interface to choose and run registered addons."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Addons")
        dialog.geometry("320x240")
        dialog.resizable(False, False)

        ttk.Label(dialog, text="Available Addons:").pack(anchor="w", padx=10, pady=5)

        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for name in self.addons.keys():
            listbox.insert(tk.END, name)

        def on_run():
            selection = listbox.curselection()
            if selection:
                addon_name = listbox.get(selection[0])
                self.run_addon_async(addon_name)
                dialog.destroy()

        ttk.Button(dialog, text="Run Selected", command=on_run).pack(pady=8)

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_discover_addons(self):
        discovered = {}
        if os.path.exists(self.addons_dir):
            for file in os.listdir(self.addons_dir):
                if file.endswith(".py") and not file.startswith("__"):
                    name = file[:-3].replace("_", " ").title()
                    discovered[name] = os.path.join(self.addons_dir, file)

        self.task_queue.put(("discovered", discovered))

    def _worker_execute_addon(self, addon_name, script_path, text_content):
        try:
            # Dynamically import and execute run(text) entrypoint in script
            spec = importlib.util.spec_from_file_location("dynamic_addon", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                result_text = module.run(text_content)
                self.task_queue.put(("addon_success", {
                    "name": addon_name,
                    "result": result_text
                }))
            else:
                self.task_queue.put(("error", f"Addon '{addon_name}' missing 'run(text)' entrypoint function."))
        except Exception as e:
            self.task_queue.put(("error", f"Error executing '{addon_name}': {str(e)}"))

    # ================================
    # Queue Dispatcher
    # ================================

    def _process_queue(self):
        try:
            while True:
                action, payload = self.task_queue.get_nowait()
                if action == "discovered":
                    self.addons = payload
                elif action == "addon_success":
                    if payload["result"] is not None and self.set_editor_text_fn:
                        self.set_editor_text_fn(payload["result"])
                    messagebox.showinfo("Addon Executed", f"Addon '{payload['name']}' completed successfully.")
                elif action == "error":
                    messagebox.showerror("Addon Error", payload)
        except queue.Empty:
            pass

        self.root.after(50, self._process_queue)
