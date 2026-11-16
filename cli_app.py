"""PyInstaller entry point for step2glb-cli.exe (console, command line only)."""

import multiprocessing
import sys

from step2glb.cli import run

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(run(sys.argv[1:]))
