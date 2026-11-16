"""PyInstaller entry point for STEP2GLB.exe (windowed: no console window)."""

import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from step2glb.__main__ import clean_argv

    argv = clean_argv(sys.argv[1:])
    if any(a.startswith("-") for a in argv):
        # A windowed exe has no console to print to: point to the command-line exe instead.
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "STEP to GLB",
            "Command-line options are handled by step2glb-cli.exe, in the same folder.\n\n"
            "Example:\n  step2glb-cli.exe model.step -q draft",
        )
        sys.exit(2)

    from step2glb.gui import run

    run(argv)
