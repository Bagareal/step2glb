"""Small Tk window: add files, pick quality, click Convert."""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .converter import (
    QUALITY_PRESETS,
    ConversionError,
    Options,
    collect_inputs,
    convert,
    default_output_path,
)

QUALITY_LABELS = {
    "Draft (fastest, smallest)": "draft",
    "Normal (recommended)": "normal",
    "Fine (slowest, largest)": "fine",
}


class App(tk.Tk):
    def __init__(self, initial_paths=None):
        super().__init__()
        self.title(f"STEP to GLB {__version__}")
        self.geometry("720x560")
        self.minsize(560, 420)
        self.files: list[str] = []
        self.msgs: "queue.Queue[tuple]" = queue.Queue()
        self.running = False
        self.out_dir = tk.StringVar(value="")
        self.same_folder = tk.BooleanVar(value=True)
        self.quality = tk.StringVar(value="Normal (recommended)")
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)
        if initial_paths:
            self._add(initial_paths)
            if self.files:
                self.after(300, self._start)

    # ---- layout ----
    def _build(self):
        pad = {"padx": 10, "pady": 4}
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, **pad)

        ttk.Label(top, text="1. Add STEP files or folders").pack(anchor="w")
        row = ttk.Frame(top)
        row.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(row, height=8, selectmode="extended")
        sb = ttk.Scrollbar(row, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        btns = ttk.Frame(row)
        btns.pack(side="left", fill="y", padx=(8, 0))
        self.btn_files = ttk.Button(btns, text="Add files...", command=self._pick_files)
        self.btn_folder = ttk.Button(btns, text="Add folder...", command=self._pick_folder)
        self.btn_remove = ttk.Button(btns, text="Remove selected", command=self._remove)
        self.btn_clear = ttk.Button(btns, text="Clear", command=self._clear)
        for b in (self.btn_files, self.btn_folder, self.btn_remove, self.btn_clear):
            b.pack(fill="x", pady=2)

        opt = ttk.LabelFrame(self, text="2. Options")
        opt.pack(fill="x", **pad)
        ttk.Label(opt, text="Quality:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.cb_quality = ttk.Combobox(opt, textvariable=self.quality, state="readonly",
                                       values=list(QUALITY_LABELS), width=28)
        self.cb_quality.grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(opt, text="Save GLB:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.chk_same = ttk.Checkbutton(opt, text="next to each STEP file", variable=self.same_folder,
                                        command=self._toggle_out)
        self.chk_same.grid(row=1, column=1, sticky="w")
        self.ent_out = ttk.Entry(opt, textvariable=self.out_dir, state="disabled")
        self.ent_out.grid(row=2, column=1, sticky="we", pady=(0, 6))
        self.btn_out = ttk.Button(opt, text="Choose folder...", command=self._pick_out, state="disabled")
        self.btn_out.grid(row=2, column=2, padx=8, pady=(0, 6))
        opt.columnconfigure(1, weight=1)

        run = ttk.Frame(self)
        run.pack(fill="x", **pad)
        self.btn_go = ttk.Button(run, text="3. Convert to GLB", command=self._start)
        self.btn_go.pack(side="left")
        self.bar = ttk.Progressbar(run, mode="indeterminate")
        self.bar.pack(side="left", fill="x", expand=True, padx=10)
        self.status = ttk.Label(run, text="Ready")
        self.status.pack(side="left")

        self.log = tk.Text(self, height=9, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, **pad)

    # ---- file list ----
    def _add(self, paths):
        new = collect_inputs(paths, recursive=True)
        for f in new:
            if f not in self.files:
                self.files.append(f)
                self.listbox.insert("end", f)
        if not new and paths:
            messagebox.showinfo("STEP to GLB", "No .step / .stp files found in the selection.")

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
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)
            del self.files[i]

    def _clear(self):
        self.listbox.delete(0, "end")
        self.files.clear()

    def _toggle_out(self):
        state = "disabled" if self.same_folder.get() else "normal"
        self.ent_out.configure(state=state)
        self.btn_out.configure(state=state)

    def _pick_out(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.out_dir.set(d)

    # ---- conversion ----
    def _set_busy(self, busy: bool):
        self.running = busy
        state = "disabled" if busy else "normal"
        for w in (self.btn_files, self.btn_folder, self.btn_remove, self.btn_clear,
                  self.btn_go, self.chk_same):
            w.configure(state=state)
        self.cb_quality.configure(state="disabled" if busy else "readonly")
        if busy:
            self.bar.start(12)
        else:
            self.bar.stop()

    def _start(self):
        if self.running:
            return
        if not self.files:
            messagebox.showinfo("STEP to GLB", "Add at least one STEP file first.")
            return
        out = None if self.same_folder.get() else self.out_dir.get().strip()
        if not self.same_folder.get() and not out:
            messagebox.showinfo("STEP to GLB", "Choose an output folder, or save next to the STEP files.")
            return
        opts = Options(quality=QUALITY_LABELS[self.quality.get()])
        files = list(self.files)
        self._set_busy(True)
        threading.Thread(target=self._worker, args=(files, out, opts), daemon=True).start()

    def _worker(self, files, out, opts):
        ok = 0
        for i, src in enumerate(files, 1):
            self.msgs.put(("status", f"File {i}/{len(files)}"))
            self.msgs.put(("log", f"\n[{i}/{len(files)}] {src}"))
            try:
                convert(src, default_output_path(src, out), opts, log=lambda m: self.msgs.put(("log", "  " + m)))
                ok += 1
            except ConversionError as e:
                self.msgs.put(("log", f"  ERROR: {e}"))
            except Exception as e:
                self.msgs.put(("log", f"  ERROR: {type(e).__name__}: {e}"))
        self.msgs.put(("done", (ok, len(files))))

    def _poll(self):
        try:
            while True:
                kind, val = self.msgs.get_nowait()
                if kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", val + "\n")
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "status":
                    self.status.configure(text=val)
                elif kind == "done":
                    ok, total = val
                    self._set_busy(False)
                    self.status.configure(text=f"Done: {ok}/{total} converted")
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
