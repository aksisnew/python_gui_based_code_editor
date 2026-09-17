import sys
import tkinter as tk
from gui import MainGUI


def main():
    """
    entry
    """
    root = tk.Tk()

    # Optional platform-specific scaling tweaks
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # Launch main application GUI
    app = MainGUI(root)
    
    # Start main Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()
