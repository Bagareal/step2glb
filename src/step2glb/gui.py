"""The STEP2GLB window: drop files, pick quality, click Convert."""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .theme import PALETTE as P
from .theme import apply_theme, dark_title_bar

QUALITY_LABELS = {
    "Draft (fastest, smallest)": "draft",
    "Normal (recommended)": "normal",
    "Fine (slowest, largest)": "fine",
}

STATUS_TEXT = {
    "queued": "Waiting",
    "running": "Converting…",
    "done": "✓ Done",
    "error": "Error",
}


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    v = float(n)
    for unit in ("KB", "MB", "GB", "TB"):
        v /= 1024
        if v < 1024 or unit == "TB":
            return f"{v:.1f} {unit}" if v < 10 else f"{v:.0f} {unit}"
    return f"{n} B"  # unreachable


def _load_dnd(root: tk.Tk):
    """Load tkdnd into this Tk; return the DND_FILES type, or None if unavailable."""
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD

        TkinterDnD._require(root)
        return DND_FILES
    except Exception:
        return None


class DropZone(tk.Canvas):
    """Dashed rounded box that hosts the 'add' controls and lights up on drag-over."""

    RADIUS = 14

    def __init__(self, master, height=128):
        super().__init__(master, height=height, bg=P["bg"], highlightthickness=0, bd=0)
        self.inner = ttk.Frame(self, style="Card.TFrame")
        self._win = self.create_window(0, 0, window=self.inner)
        self._hot = False
        self.bind("<Configure>", lambda e: self._draw())

    def set_hot(self, hot: bool):
        self._hot = hot
        self._draw()

    def _draw(self):
        self.delete("box")
        w, h, r, m = self.winfo_width(), self.winfo_height(), self.RADIUS, 2
        x0, y0, x1, y1 = m, m, w - m, h - m
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
               x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        self.create_polygon(
            pts, smooth=True, tags="box", fill=P["surface"],
            outline=P["accent"] if self._hot else P["muted"], width=1.5,
            dash=() if self._hot else (6, 4))
        self.tag_lower("box")
        self.coords(self._win, w / 2, h / 2)


class App(tk.Tk):
    def __init__(self, initial_paths=None):
        super().__init__()
        self.withdraw()
        self.title("STEP to GLB")
        self.geometry("780x720")
        self.minsize(620, 600)
        self.fonts = apply_theme(self)
        self.dnd = _load_dnd(self)

        self.files: list[str] = []
        self.row_state: dict[str, str] = {}
        self.errors: dict[str, str] = {}
        self.msgs: "queue.Queue[tuple]" = queue.Queue()
        self.running = False
        self.out_dir = tk.StringVar(value="")
        self.save_mode = tk.StringVar(value="same")
        self.quality = tk.StringVar(value="Normal (recommended)")
        self.details_open = False

        self._build()
        self._update_empty()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        if sys.platform == "darwin":
            self.createcommand("::tk::mac::OpenDocument", self._open_documents)
        self.after(100, self._poll)
        self.deiconify()
        dark_title_bar(self)
        if initial_paths:
            self._add(initial_paths)
            if self.files:
                self.after(300, self._start)

    # ---- layout ----
    def _build(self):
        root = ttk.Frame(self, padding=(22, 18, 22, 16))
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        head = ttk.Frame(root)
        head.grid(row=0, column=0, sticky="we", pady=(0, 14))
        ttk.Label(head, text="STEP to GLB", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text=f"v{__version__}", style="Muted.TLabel").pack(side="left", padx=10, pady=(8, 0))

        # Drop zone
        self.drop = DropZone(root)
        self.drop.grid(row=1, column=0, sticky="we")
        z = self.drop.inner
        msg = "Drop .step / .stp files or folders here" if self.dnd else "Add .step / .stp files or folders"
        ttk.Label(z, text=msg, style="Card.TLabel", font=self.fonts["big"]).pack(pady=(0, 4))
        ttk.Label(z, text="Large CAD files are converted one after the other",
                  style="Card.TLabel", foreground=P["muted"], font=self.fonts["small"]).pack(pady=(0, 12))
        zb = ttk.Frame(z, style="Card.TFrame")
        zb.pack()
        self.btn_files = ttk.Button(zb, text="Add files…", command=self._pick_files)
        self.btn_folder = ttk.Button(zb, text="Add folder…", command=self._pick_folder)
        self.btn_files.pack(side="left", padx=4)
        self.btn_folder.pack(side="left", padx=4)

        # File list
        card = ttk.Frame(root, style="Card.TFrame", padding=(6, 4, 0, 4))
        card.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        root.rowconfigure(2, weight=1)
        self.tree = ttk.Treeview(card, columns=("size", "status"), show="tree headings",
                                 selectmode="extended")
        self.tree.heading("#0", text="FILE", anchor="w")
        self.tree.heading("size", text="SIZE", anchor="e")
        self.tree.heading("status", text="STATUS", anchor="w")
        self.tree.column("#0", stretch=True, minwidth=200)
        self.tree.column("size", width=90, stretch=False, anchor="e")
        self.tree.column("status", width=140, stretch=False, anchor="w")
        self.tree.tag_configure("queued", foreground=P["muted"])
        self.tree.tag_configure("running", foreground=P["accent"])
        self.tree.tag_configure("done", foreground=P["success"])
        self.tree.tag_configure("error", foreground=P["error"])
        sb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._show_selection())
        self.tree.bind("<Delete>", lambda e: self._remove())
        self.empty = ttk.Label(card, text="No files yet", style="Card.TLabel", foreground=P["muted"])

        row = ttk.Frame(root)
        row.grid(row=3, column=0, sticky="we", pady=(6, 0))
        self.path_label = ttk.Label(row, text="", style="Muted.TLabel", anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True)
        self.btn_clear = ttk.Button(row, text="Clear", style="Link.TButton", command=self._clear)
        self.btn_remove = ttk.Button(row, text="Remove selected", style="Link.TButton", command=self._remove)
        self.btn_clear.pack(side="right", padx=(12, 0))
        self.btn_remove.pack(side="right")

        # Options
        opt = ttk.Frame(root)
        opt.grid(row=4, column=0, sticky="we", pady=(12, 0))
        opt.columnconfigure(2, weight=1)
        ttk.Label(opt, text="Quality", style="Section.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 16), pady=4)
        self.cb_quality = ttk.Combobox(opt, textvariable=self.quality, state="readonly",
                                       values=list(QUALITY_LABELS), width=26)
        self.cb_quality.grid(row=0, column=1, columnspan=2, sticky="w", pady=4)
        ttk.Label(opt, text="Save to", style="Section.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 16), pady=4)
        self.rb_same = ttk.Radiobutton(opt, text="Next to each STEP file", value="same",
                                       variable=self.save_mode, command=self._toggle_out)
        self.rb_same.grid(row=1, column=1, columnspan=3, sticky="w", pady=4)
        self.rb_dir = ttk.Radiobutton(opt, text="Folder", value="dir",
                                      variable=self.save_mode, command=self._toggle_out)
        self.rb_dir.grid(row=2, column=1, sticky="w", pady=4)
        self.ent_out = ttk.Entry(opt, textvariable=self.out_dir, state="disabled")
        self.ent_out.grid(row=2, column=2, sticky="we", padx=(10, 8), pady=4)
        self.btn_out = ttk.Button(opt, text="Choose…", command=self._pick_out, state="disabled")
        self.btn_out.grid(row=2, column=3, pady=4)

        # Progress + convert
        run = ttk.Frame(root)
        run.grid(row=5, column=0, sticky="we", pady=(16, 0))
        left = ttk.Frame(run)
        left.pack(side="left", fill="x", expand=True, padx=(0, 18))
        self.status = ttk.Label(left, text="Ready", style="Muted.TLabel")
        self.status.pack(anchor="w", pady=(0, 6))
        self.bar = ttk.Progressbar(left, mode="determinate", maximum=100)
        self.bar.pack(fill="x")
        self.btn_go = ttk.Button(run, text="Convert to GLB", style="Accent.TButton", command=self._start)
        self.btn_go.pack(side="right")

        # Details (log)
        self.btn_details = ttk.Button(root, text="▸ Details", style="Link.TButton", command=self._toggle_details)
        self.btn_details.grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.log = tk.Text(root, height=8, state="disabled", wrap="word", bg=P["surface"], fg=P["muted"],
                           insertbackground=P["text"], relief="flat", bd=0, highlightthickness=0,
                           padx=12, pady=10, font=(self.fonts["mono"], self.fonts["size"] - 1),
                           selectbackground=P["select"])
        self.log.grid(row=7, column=0, sticky="nsew", pady=(4, 0))
        self.log.grid_remove()
        self._log_row = root
        self._toggle_out()

        if self.dnd:
            for w in (self.drop, z, zb, self.tree, card, *z.winfo_children()):
                try:
                    w.drop_target_register(self.dnd)
                    w.dnd_bind("<<DropEnter>>", self._drag_enter)
                    w.dnd_bind("<<DropLeave>>", self._drag_leave)
                    w.dnd_bind("<<Drop>>", self._drop)
                except Exception:
                    pass

    # ---- drag and drop ----
    def _drag_enter(self, event):
        if not self.running:
            self.drop.set_hot(True)
        return event.action

    def _drag_leave(self, event):
        self.drop.set_hot(False)
        return event.action

    def _drop(self, event):
        self.drop.set_hot(False)
        if not self.running:
            self._add(list(self.tk.splitlist(event.data)))
        return event.action

    def _open_documents(self, *paths):
        self._add(list(paths))
        if self.files and not self.running:
            self.after(300, self._start)

    # ---- file list ----
    def _add(self, paths):
        from .converter import collect_inputs

        new = collect_inputs(paths, recursive=True)
        for f in new:
            if f in self.row_state:
                continue
            self.files.append(f)
            try:
                size = format_size(os.path.getsize(f))
            except OSError:
                size = ""
            self.tree.insert("", "end", iid=f, text="  " + os.path.basename(f), values=(size, ""))
            self._set_row(f, "queued")
        if not new and paths:
            messagebox.showinfo("STEP to GLB", "No .step / .stp files found in the selection.")
        self._update_empty()

    def _set_row(self, path, state, error=""):
        self.row_state[path] = state
        if error:
            self.errors[path] = error
        else:
            self.errors.pop(path, None)
        if self.tree.exists(path):
            self.tree.item(path, tags=(state,))
            self.tree.set(path, "status", STATUS_TEXT[state])
            if state == "running":
                self.tree.see(path)
        self._show_selection()

    def _update_empty(self):
        if self.files:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")

    def _show_selection(self):
        sel = self.tree.selection()
        if len(sel) == 1:
            path = sel[0]
            err = self.errors.get(path)
            self.path_label.configure(text=f"Error: {err}  ·  {os.path.normpath(path)}" if err else os.path.normpath(path),
                                      foreground=P["error"] if err else P["muted"])
        elif sel:
            self.path_label.configure(text=f"{len(sel)} files selected", foreground=P["muted"])
        else:
            n = len(self.files)
            self.path_label.configure(text=f"{n} file{'s' if n != 1 else ''}" if n else "",
                                      foreground=P["muted"])

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Select STEP files",
            filetypes=[("STEP files", "*.step *.stp *.STEP *.STP"), ("All files", "*.*")])
        if paths:
            self._add(list(paths))

    def _pick_folder(self):
        d = filedialog.askdirectory(title="Select a folder containing STEP files")
        if d:
            self._add([d])

    def _remove(self):
        if self.running:
            return
        for path in self.tree.selection():
            self.tree.delete(path)
            self.files.remove(path)
            self.row_state.pop(path, None)
            self.errors.pop(path, None)
        self._update_empty()
        self._show_selection()

    def _clear(self):
        if self.running:
            return
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self.row_state.clear()
        self.errors.clear()
        self.bar.configure(value=0)
        self.status.configure(text="Ready", foreground=P["muted"])
        self._update_empty()
        self._show_selection()

    def _toggle_out(self):
        state = "normal" if self.save_mode.get() == "dir" and not self.running else "disabled"
        self.ent_out.configure(state=state)
        self.btn_out.configure(state=state)

    def _pick_out(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.out_dir.set(d)

    def _toggle_details(self):
        self.details_open = not self.details_open
        if self.details_open:
            self.log.grid()
            self._log_row.rowconfigure(7, weight=1)
            if self.state() == "normal":
                self.geometry(f"{self.winfo_width()}x{self.winfo_height() + 170}")
            self.btn_details.configure(text="▾ Details")
        else:
            self.log.grid_remove()
            self._log_row.rowconfigure(7, weight=0)
            if self.state() == "normal":
                self.geometry(f"{self.winfo_width()}x{max(600, self.winfo_height() - 170)}")
            self.btn_details.configure(text="▸ Details")

    # ---- conversion ----
    def _set_busy(self, busy: bool):
        self.running = busy
        state = "disabled" if busy else "normal"
        for w in (self.btn_files, self.btn_folder, self.btn_remove, self.btn_clear,
                  self.btn_go, self.rb_same, self.rb_dir):
            w.configure(state=state)
        self.cb_quality.configure(state="disabled" if busy else "readonly")
        self.btn_go.configure(text="Converting…" if busy else "Convert to GLB")
        self._toggle_out()

    def _start(self):
        from .converter import Options

        if self.running:
            return
        if not self.files:
            messagebox.showinfo("STEP to GLB", "Add at least one STEP file first.")
            return
        out = None
        if self.save_mode.get() == "dir":
            out = self.out_dir.get().strip()
            if not out:
                messagebox.showinfo("STEP to GLB", "Choose an output folder, or save next to the STEP files.")
                return
        opts = Options(quality=QUALITY_LABELS[self.quality.get()])
        files = list(self.files)
        for f in files:
            self._set_row(f, "queued")
        self.bar.configure(value=0)
        self.status.configure(text=f"0 of {len(files)}", foreground=P["muted"])
        self._set_busy(True)
        threading.Thread(target=self._worker, args=(files, out, opts), daemon=True).start()

    def _worker(self, files, out, opts):
        from .converter import ConversionError, convert, default_output_path

        ok = 0
        total = len(files)
        for i, src in enumerate(files, 1):
            self.msgs.put(("row", (src, "running", "")))
            self.msgs.put(("status", f"Converting {i} of {total}  ·  {os.path.basename(src)}"))
            self.msgs.put(("log", f"\n[{i}/{total}] {src}"))
            try:
                convert(src, default_output_path(src, out), opts,
                        log=lambda m: self.msgs.put(("log", "  " + m)))
                ok += 1
                self.msgs.put(("row", (src, "done", "")))
            except ConversionError as e:
                self.msgs.put(("log", f"  ERROR: {e}"))
                self.msgs.put(("row", (src, "error", str(e))))
            except Exception as e:
                self.msgs.put(("log", f"  ERROR: {type(e).__name__}: {e}"))
                self.msgs.put(("row", (src, "error", f"{type(e).__name__}: {e}")))
            self.msgs.put(("progress", i * 100 / total))
        self.msgs.put(("done", (ok, total)))

    def _poll(self):
        try:
            while True:
                kind, val = self.msgs.get_nowait()
                if kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", val + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "row":
                    self._set_row(*val)
                elif kind == "progress":
                    self.bar.configure(value=val)
                elif kind == "status":
                    self.status.configure(text=val)
                elif kind == "done":
                    ok, total = val
                    self._set_busy(False)
                    if ok == total:
                        self.status.configure(text=f"Done  ·  {ok} of {total} converted", foreground=P["success"])
                    else:
                        self.status.configure(text=f"{ok} of {total} converted  ·  {total - ok} failed "
                                                   "(select a file to see why)", foreground=P["error"])
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _on_close(self):
        if self.running and not messagebox.askyesno(
                "STEP to GLB", "A conversion is still running. Quit anyway?"):
            return
        os._exit(0) if self.running else self.destroy()


def run(initial_paths=None):
    App(initial_paths).mainloop()
