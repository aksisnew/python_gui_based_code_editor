import os
import queue
import shutil
import threading


class FileManager:
    def __init__(self, ui_callback=None):
        """
    kind of multi threaded handeling for files
        """
        self.ui_callback = ui_callback
        self.task_queue = queue.Queue()



    def save_file_async(self, file_path, content, overwrite=False):
        """Saves content to disk in a background thread."""
        threading.Thread(
            target=self._worker_save, 
            args=(file_path, content, overwrite), 
            daemon=True
        ).start()

    def rename_file_async(self, old_path, new_path):
        """Renames a file asynchronously and checks for existing target conflicts."""
        threading.Thread(
            target=self._worker_rename, 
            args=(old_path, new_path), 
            daemon=True
        ).start()

    def delete_file_async(self, file_path):
        """Deletes a file asynchronously."""
        threading.Thread(
            target=self._worker_delete, 
            args=(file_path,), 
            daemon=True
        ).start()

    # ================================
    # Multi-Threaded Workers
    # ================================

    def _worker_save(self, file_path, content, overwrite):
        if os.path.exists(file_path) and not overwrite:
            self._dispatch_event("conflict", {
                "action": "save",
                "file_path": file_path,
                "message": f"File '{file_path}' already exists. Overwrite?"
            })
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._dispatch_event("save_success", {
                "file_path": file_path,
                "message": f"Successfully saved: {os.path.basename(file_path)}"
            })
        except Exception as e:
            self._dispatch_event("error", {
                "action": "save",
                "message": f"Failed to save file: {str(e)}"
            })

    def _worker_rename(self, old_path, new_path):
        if not os.path.exists(old_path):
            self._dispatch_event("error", {
                "action": "rename",
                "message": f"Source file does not exist: {old_path}"
            })
            return

        if os.path.exists(new_path):
            self._dispatch_event("conflict", {
                "action": "rename",
                "old_path": old_path,
                "new_path": new_path,
                "message": f"Target file '{new_path}' already exists."
            })
            return

        try:
            os.rename(old_path, new_path)
            self._dispatch_event("rename_success", {
                "old_path": old_path,
                "new_path": new_path,
                "message": f"Renamed to {os.path.basename(new_path)}"
            })
        except Exception as e:
            self._dispatch_event("error", {
                "action": "rename",
                "message": f"Failed to rename file: {str(e)}"
            })

    def _worker_delete(self, file_path):
        if not os.path.exists(file_path):
            self._dispatch_event("error", {
                "action": "delete",
                "message": f"File not found: {file_path}"
            })
            return

        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            self._dispatch_event("delete_success", {
                "file_path": file_path,
                "message": f"Deleted: {os.path.basename(file_path)}"
            })
        except Exception as e:
            self._dispatch_event("error", {
                "action": "delete",
                "message": f"Failed to delete file: {str(e)}"
            })

    def _dispatch_event(self, event_type, payload):
        """dictionary back to UI callback."""
        if self.ui_callback:
            payload["event"] = event_type
            self.ui_callback(payload)
