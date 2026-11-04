"""
AutoTyper Pro - Main Entry Point.
Runs the GUI application with global hotkeys and Windows SendInput engine.
"""

import sys
import tkinter as tk
from autotyper.gui import AutoTyperGUI


def main():
    root = tk.Tk()
    app = AutoTyperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
