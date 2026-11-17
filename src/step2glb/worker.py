"""Runs one conversion in a child process.

OpenCASCADE keeps Python's interpreter lock for the whole length of each call
(reading, meshing, writing), so a conversion running in a thread of the window's
process freezes the window. In its own process it cannot: the window only reads
the messages this process sends through a pipe. It also frees all the memory of a large file
when the conversion ends, and the window can stop it at any time.
"""

from __future__ import annotations

import os
import sys


def lower_priority() -> None:
    """Let other programs go first, so the computer stays usable while all cores work."""
    try:
        if sys.platform == "win32":
            import ctypes

            BELOW_NORMAL_PRIORITY_CLASS = 0x4000
            k32 = ctypes.windll.kernel32
            k32.SetPriorityClass(k32.GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS)
        else:
            os.nice(10)
    except Exception:
        pass


def run_job(src, dst, opts, conn) -> None:
    """Convert src to dst and report through conn, the sending end of a Pipe.

    Messages: ("log", text), ("phase", (phase, fraction or None)),
    then exactly one of ("ok", stats) or ("error", text).
    A Pipe and not a multiprocessing.Queue: a Queue sends from a background
    thread, which OpenCASCADE would block, so messages would arrive late.
    """
    lower_priority()
    send = conn.send
    try:
        from .converter import ConversionError, convert

        stats = convert(src, dst, opts,
                        log=lambda m: send(("log", m)),
                        progress=lambda p, f: send(("phase", (p, f))))
        send(("ok", stats))
    except ConversionError as e:
        send(("error", str(e)))
    except Exception as e:  # noqa: BLE001 - anything else is reported to the window too
        send(("error", f"{type(e).__name__}: {e}"))
    finally:
        conn.close()
