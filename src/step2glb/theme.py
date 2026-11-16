"""Dark ttk theme: the built-in 'clam' theme recoloured with the STEP2GLB palette."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

PALETTE = {
    "bg": "#0F1115",
    "surface": "#171A21",
    "surface2": "#1E222B",
    "hover": "#262B36",
    "border": "#262B36",
    "select": "#2A303C",
    "text": "#E6E8EC",
    "muted": "#8B93A1",
    "accent": "#ECE9E2",
    "accent_hover": "#F6F4EF",
    "accent_pressed": "#D6D2C9",
    "on_accent": "#0F1115",
    "disabled": "#3A3F4A",
    "success": "#7FD49B",
    "error": "#FF7A7A",
}


def _fonts(root: tk.Misc) -> dict:
    base = tkfont.nametofont("TkDefaultFont", root)
    family = base.actual("family")
    size = 10 if sys.platform == "win32" else 13
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name, root).configure(family=family, size=size)
    return {
        "base": (family, size),
        "bold": (family, size, "bold"),
        "small": (family, size - 1),
        "title": (family, size + 6, "bold"),
        "big": (family, size + 1),
        "mono": tkfont.nametofont("TkFixedFont", root).actual("family"),
        "size": size,
    }


def dark_title_bar(root: tk.Tk) -> None:
    """Ask the OS for a dark window frame (best effort)."""
    try:
        if sys.platform == "win32":
            import ctypes

            root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            value = ctypes.c_int(1)
            for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (new / old builds)
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                    break
        elif sys.platform == "darwin":
            root.tk.call("::tk::unsupported::MacWindowStyle", "appearance", root, "darkaqua")
    except Exception:
        pass


def apply_theme(root: tk.Tk) -> dict:
    """Style every ttk widget used by the app. Returns the font set."""
    p = PALETTE
    f = _fonts(root)
    root.configure(bg=p["bg"])
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=p["bg"], foreground=p["text"], fieldbackground=p["surface"],
                bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                troughcolor=p["surface"], selectbackground=p["select"],
                selectforeground=p["text"], insertcolor=p["text"], focuscolor=p["border"],
                font=f["base"])
    s.map(".", foreground=[("disabled", p["muted"])])

    s.configure("TFrame", background=p["bg"])
    s.configure("Card.TFrame", background=p["surface"])
    s.configure("TLabel", background=p["bg"], foreground=p["text"])
    s.configure("Card.TLabel", background=p["surface"])
    s.configure("Muted.TLabel", foreground=p["muted"], font=f["small"])
    s.configure("Title.TLabel", font=f["title"])
    s.configure("Section.TLabel", foreground=p["muted"], font=f["bold"])

    # Buttons
    s.configure("TButton", background=p["surface2"], foreground=p["text"], bordercolor=p["border"],
                lightcolor=p["surface2"], darkcolor=p["surface2"], relief="flat",
                padding=(14, 7), focusthickness=0)
    s.map("TButton",
          background=[("disabled", p["bg"]), ("pressed", p["select"]), ("active", p["hover"])],
          lightcolor=[("pressed", p["select"]), ("active", p["hover"])],
          darkcolor=[("pressed", p["select"]), ("active", p["hover"])],
          bordercolor=[("disabled", p["surface2"])])
    s.configure("Accent.TButton", background=p["accent"], foreground=p["on_accent"],
                bordercolor=p["accent"], lightcolor=p["accent"], darkcolor=p["accent"],
                font=f["bold"], padding=(22, 9))
    s.map("Accent.TButton",
          background=[("disabled", p["disabled"]), ("pressed", p["accent_pressed"]),
                      ("active", p["accent_hover"])],
          lightcolor=[("disabled", p["disabled"]), ("pressed", p["accent_pressed"]),
                      ("active", p["accent_hover"])],
          darkcolor=[("disabled", p["disabled"]), ("pressed", p["accent_pressed"]),
                     ("active", p["accent_hover"])],
          bordercolor=[("disabled", p["disabled"]), ("pressed", p["accent_pressed"]),
                       ("active", p["accent_hover"])],
          foreground=[("disabled", p["muted"])])
    s.configure("Link.TButton", background=p["bg"], foreground=p["muted"], bordercolor=p["bg"],
                lightcolor=p["bg"], darkcolor=p["bg"], padding=(0, 4))
    s.map("Link.TButton", background=[("active", p["bg"])], foreground=[("active", p["text"])],
          lightcolor=[("active", p["bg"])], darkcolor=[("active", p["bg"])])

    # Radio / check
    for w in ("TRadiobutton", "TCheckbutton"):
        s.configure(w, background=p["bg"], foreground=p["text"], indicatorbackground=p["surface"],
                    indicatorforeground=p["on_accent"], upperbordercolor=p["border"],
                    lowerbordercolor=p["border"], indicatormargin=(0, 0, 8, 0), focusthickness=0)
        s.map(w, background=[("active", p["bg"])],
              indicatorbackground=[("selected", p["accent"]), ("active", p["hover"])],
              upperbordercolor=[("selected", p["accent"])],
              lowerbordercolor=[("selected", p["accent"])])

    # Entry / combobox
    s.configure("TEntry", fieldbackground=p["surface"], foreground=p["text"], padding=6,
                bordercolor=p["border"], lightcolor=p["surface"], darkcolor=p["surface"])
    s.map("TEntry", fieldbackground=[("disabled", p["bg"])], bordercolor=[("focus", p["muted"])],
          lightcolor=[("focus", p["surface"])])
    s.configure("TCombobox", fieldbackground=p["surface"], background=p["surface2"],
                foreground=p["text"], arrowcolor=p["text"], bordercolor=p["border"],
                lightcolor=p["surface"], darkcolor=p["surface"], padding=6, arrowsize=14)
    s.map("TCombobox",
          fieldbackground=[("readonly", p["surface"]), ("disabled", p["bg"])],
          background=[("active", p["hover"]), ("readonly", p["surface2"])],
          foreground=[("readonly", p["text"]), ("disabled", p["muted"])],
          selectbackground=[("readonly", p["surface"])],
          selectforeground=[("readonly", p["text"])],
          arrowcolor=[("disabled", p["muted"])])
    root.option_add("*TCombobox*Listbox.background", p["surface2"])
    root.option_add("*TCombobox*Listbox.foreground", p["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["select"])
    root.option_add("*TCombobox*Listbox.selectForeground", p["text"])
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.font", f["base"])

    # File list
    rowheight = int(f["size"] * (2.9 if sys.platform == "win32" else 2.1))
    s.configure("Treeview", background=p["surface"], fieldbackground=p["surface"],
                foreground=p["text"], bordercolor=p["surface"], lightcolor=p["surface"],
                darkcolor=p["surface"], rowheight=rowheight, borderwidth=0)
    s.map("Treeview", background=[("selected", p["select"])],
          foreground=[("selected", p["text"])])
    s.configure("Treeview.Heading", background=p["surface"], foreground=p["muted"],
                bordercolor=p["surface"], lightcolor=p["surface"], darkcolor=p["surface"],
                relief="flat", font=f["small"], padding=(8, 6))
    s.map("Treeview.Heading", background=[("active", p["surface"])])
    s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # Progress / scrollbar
    s.configure("Horizontal.TProgressbar", troughcolor=p["surface2"], background=p["accent"],
                bordercolor=p["surface2"], lightcolor=p["accent"], darkcolor=p["accent"],
                thickness=6)
    s.configure("Vertical.TScrollbar", troughcolor=p["surface"], background=p["surface2"],
                bordercolor=p["surface"], lightcolor=p["surface2"], darkcolor=p["surface2"],
                arrowcolor=p["muted"], gripcount=0, arrowsize=12)
    s.map("Vertical.TScrollbar", background=[("active", p["hover"])])
    return f
