# Modern UI and macOS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dark, modern Tk window with drag-and-drop and per-file status, plus a macOS Apple Silicon app in the same release (v1.1.0).

**Architecture:** Recoloured ttk `clam` theme in a new `theme.py`; `gui.py` rewritten around a drop zone, a `Treeview` file list and a determinate progress bar. PyInstaller spec adds `BUNDLE` on macOS; CI becomes a Windows/macOS matrix plus a release job.

**Tech Stack:** Python 3.12, tkinter/ttk, tkinterdnd2, cadquery-ocp, PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-16-modern-ui-and-macos-design.md`

## Global Constraints
- Palette: bg `#0F1115`, surface `#171A21`, border `#262B36`, text `#E6E8EC`, muted `#8B93A1`, accent `#ECE9E2`, success `#7FD49B`, error `#FF7A7A`. No glow.
- UI text stays English. Version `1.1.0`.
- Drag-and-drop is optional at runtime: if tkinterdnd2 fails to load, the app still works.
- macOS: arm64 only (`macos-14` runner), unsigned; zip with `ditto -c -k --keepParent`.

## Review Focus
- macOS passes `-psn_*` launch args: they must not trigger the "use the CLI" message → `clean_argv` test.
- Dropped paths with spaces/braces must split correctly → use `tk.splitlist` on drop data.
- Re-running a list that already has Done/Error rows resets every row to Waiting.
- A failing file marks only its row as Error; the batch continues.
- `.app` main executable must be the GUI, not the CLI → CI checks `CFBundleExecutable`.

---

### Task 1: Helpers and theme
**Files:** Create `src/step2glb/theme.py`; Modify `src/step2glb/__main__.py`; Test `tests/test_gui_helpers.py`
**Interfaces — Produces:** `theme.apply_theme(root: tk.Tk) -> None`, `theme.PALETTE: dict[str,str]`; `gui.format_size(n: int) -> str`; `__main__.clean_argv(argv: list[str]) -> list[str]` (drops `-psn_*`).
- [ ] Tests: `format_size(0)=="0 B"`, `format_size(512)=="512 B"`, `format_size(1536)=="1.5 KB"`, `format_size(204800)=="200 KB"`, `format_size(12*1024**2)=="12 MB"`; `clean_argv(["-psn_0_1","a.step"])==["a.step"]`.
- [ ] Implement, run `python -m pytest tests/test_gui_helpers.py`, commit.

### Task 2: GUI rewrite
**Files:** Modify `src/step2glb/gui.py`, `app.py`, `requirements.txt` (+`tkinterdnd2>=0.4`)
- [ ] Drop zone (Canvas, dashed border → accent when dragging over), Add files / Add folder buttons.
- [ ] Treeview: name, size, status (`Waiting`, `Converting…`, `✓ Done`, `Error`), coloured tags; selected row's full path (and error) in a muted label; Remove / Clear.
- [ ] Quality combobox; Save radios (next to STEP / folder + Choose…).
- [ ] Determinate progress "N of M", accent Convert button, collapsible Details log.
- [ ] Windows dark title bar (DWM attr 20), macOS `darkaqua`, `::tk::mac::OpenDocument`.
- [ ] Commit.

### Task 3: Packaging, CI, README, release
**Files:** Modify `STEP2GLB.spec`, `.github/workflows/build.yml`, `README.md`, version files
- [ ] Spec: `collect_all("tkinterdnd2")`; on darwin `BUNDLE(... name="STEP2GLB.app")` with STEP document types.
- [ ] CI matrix windows-latest / macos-14; mac smoke test with `STEP2GLB.app/Contents/MacOS/step2glb-cli`, plist check; release job uploads both zips on `v*` tags.
- [ ] README: Mac quick start + "macOS blocks the app" steps; bump to 1.1.0.
- [ ] Push, wait for green CI, tag `v1.1.0`, verify release has both zips.
