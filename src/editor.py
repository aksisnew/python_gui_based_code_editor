import re
import tkinter as tk
from collections import Counter


class EditorEngine:
    def __init__(self, parent_widget, bottom_bar_callback=None):
        """
       start the main editor
        """
        self.parent = parent_widget
        self.bottom_bar_callback = bottom_bar_callback
        
        # Core Tkinter Text Widget
        self.text_widget = tk.Text(
            self.parent,
            wrap=tk.NONE,
            undo=True,
            autoseparators=True
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Word prediction state
        self.word_freq = Counter()

        # Bind events to update bottombar and track text updates
        self.text_widget.bind("<<CursorChange>>", self._on_cursor_or_selection_change)
        self.text_widget.bind("<KeyRelease>", self._on_key_release)
        self.text_widget.bind("<ButtonRelease-1>", self._on_cursor_or_selection_change)



    def get_cursor_position(self):
        """Returns (line, column) tuple for current cursor location."""
        cursor_index = self.text_widget.index(tk.INSERT)
        line, col = cursor_index.split(".")
        return int(line), int(col)

    def get_stats(self):
        """
        Calculates and returns a dictionary containing line/col positions,
        total character count, selected character count, and selected line count.
        """
        line, col = self.get_cursor_position()
        total_chars = len(self.text_widget.get("1.0", tk.END)) - 1  # Exclude trailing newline
        
        selected_chars = 0
        selected_lines = 0
        
        try:
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            
            selected_text = self.text_widget.get(sel_start, sel_end)
            selected_chars = len(selected_text)
            
            start_line = int(sel_start.split(".")[0])
            end_line = int(sel_end.split(".")[0])
            selected_lines = (end_line - start_line) + 1
        except tk.TclError:
            # Triggered if no selection exists
            pass

        return {
            "line": line,
            "column": col,
            "total_chars": total_chars,
            "selected_chars": selected_chars,
            "selected_lines": selected_lines
        }

    def set_text(self, content):
        """Populates the editor with content (used when opening files)."""
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", content)
        self.update_word_frequencies()
        self._notify_bottom_bar()

    def get_text(self):
        """Retrieves all text currently in the editor."""
        return self.text_widget.get("1.0", tk.END + "-1c")



    def update_word_frequencies(self):
        """Parses the entire document text and tracks repeated words."""
        text = self.get_text()
        words = re.findall(r'\b[A-Za-z_]\w*\b', text)
        self.word_freq = Counter(words)

    def predict_next_word(self, prefix):
        """
        Suggests matching words based on frequency for a given prefix string.
        """
        if not prefix:
            return []
        
        matches = [word for word in self.word_freq if word.startswith(prefix) and word != prefix]
        matches.sort(key=lambda w: self.word_freq[w], reverse=True)
        return matches

    def get_current_word_prefix(self):
        """Extracts the word prefix directly behind the current cursor."""
        cursor_index = self.text_widget.index(tk.INSERT)
        line, col = cursor_index.split(".")
        line_text = self.text_widget.get(f"{line}.0", cursor_index)
        
        match = re.search(r'([A-Za-z_]\w*)$', line_text)
        return match.group(1) if match else ""

  
    def _on_key_release(self, event):
        """Updates word frequencies periodically and notifies bottombar listeners."""
        # Update word frequency mapping on space or newline insertions
        if event.keysym in ("space", "Return"):
            self.update_word_frequencies()
            
        self._notify_bottom_bar()

    def _on_cursor_or_selection_change(self, event=None):
        """cursor detection"""
        self._notify_bottom_bar()

    def _notify_bottom_bar(self):
        """send data to respective apis"""
        if self.bottom_bar_callback:
            stats = self.get_stats()
            self.bottom_bar_callback(stats)
