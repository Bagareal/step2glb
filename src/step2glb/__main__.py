"""Entry point: GUI by default, command line when options (--something) are given."""

import sys


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if any(a.startswith("-") for a in argv):
        from .cli import run
        return run(argv)

    # GUI: also used when files/folders are dragged onto the .exe.
    if sys.platform == "win32":
        try:  # hide the console window that comes with the exe
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass
    from .gui import run
    run(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
