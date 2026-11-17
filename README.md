# STEP2GLB

Portable **STEP / STP to GLB** converter for **Windows** and **macOS** (Apple Silicon).
No installation, no Python, no admin rights: download a zip, extract it anywhere, run it.

It is built on [OpenCASCADE](https://dev.opencascade.org/) (the same CAD kernel used by FreeCAD)
and is meant for large CAD files that are too heavy to open directly in a browser-based 3D viewer.

## Quick start

### Windows

1. Download `STEP2GLB-windows-x64.zip` from the [Releases](../../releases) page and extract it
   (a USB stick or any folder you can write to is fine).
2. Run `STEP2GLB.exe`, then either:
   - **drag `.step` / `.stp` files (or folders) into the window**, or onto `STEP2GLB.exe`, or
   - click **Add files…** / **Add folder…**, then **Convert to GLB**.
3. The `.glb` files appear next to the STEP files (or in the folder you chose).

### macOS (Apple Silicon: M1 or newer)

1. Download `STEP2GLB-macos-arm64.zip` from the [Releases](../../releases) page and open it:
   you get `STEP2GLB.app`. Move it to *Applications* or anywhere you like.
2. Open it. **The first time, macOS will probably block it**: see
   [macOS says the app can't be opened](#macos-says-the-app-cant-be-opened) below.
3. Drag `.step` / `.stp` files into the window (or onto the app icon), then **Convert to GLB**.

Intel Macs are not supported.

### Using the window

Every file in the list shows its own status: *Waiting*, the step it is at, *✓ Done*, *Error* or
*Cancelled*. Select a file that failed to see why. Files are converted one after the other; the line
above the bar shows which one, the current step and the time spent on it. **Details** opens the full
conversion log.

A conversion goes through four steps:

| Step | Bar |
| --- | --- |
| Reading file… | Moving, without a percentage: OpenCASCADE gives no progress for this step |
| Building shapes… | Moving, without a percentage (same reason) |
| Meshing 0–100% | Real percentage: parts are meshed one by one |
| Writing GLB… | Moving, then full |

On large files the first two steps take most of the time. The window stays usable during the
whole conversion: each file is converted in a separate background process, which also frees all
its memory when the file is done. **Cancel** stops the current file at once (no half-written GLB
is left behind). The converter runs at low priority: it uses every CPU core, but other programs go
first, so the computer stays responsive.

## What is kept in the GLB

| Kept | Notes |
| --- | --- |
| Assembly hierarchy | Parts and sub-assemblies stay separate nodes, so you can select or hide them individually |
| Part names | Product name first, instance name as a fallback |
| Colours | As defined in the STEP file |
| Repeated parts | A part used many times is stored once and instanced, which keeps files small |
| One mesh per part | The faces of a part are merged (one piece per colour), so viewers show and explode whole parts, not separate faces, and stay fast |
| Units and axes | Metres and Y-up, as the glTF standard requires (STEP files are usually millimetres, Z-up) |

Not included: textures, animations, product manufacturing information (PMI / annotations) and
Draco / meshopt compression. The output is a plain, uncompressed GLB.

## Quality presets

| Preset | Use it for |
| --- | --- |
| Draft | Very large files, quick previews, smallest GLB |
| Normal (default) | Good looking result for most files |
| Fine | Close-up inspection of smooth, curved parts (slower, larger file) |

The presets are relative to the size of each part, so a small screw and a large housing both keep
a good shape. If a file still fails or is too big, convert it with **Draft** first.

## Command line

`STEP2GLB.exe` is the window only (it opens no console). For scripts and batch jobs use
`step2glb-cli.exe`, which is in the same folder. On macOS the command line tool is
`STEP2GLB.app/Contents/MacOS/step2glb-cli`. Run it from a terminal:

```
step2glb-cli.exe model.step
step2glb-cli.exe D:\cad\models -r -q draft -o D:\cad\glb --skip-existing
```

| Option | Meaning |
| --- | --- |
| `-o, --out-dir DIR` | Write GLB files to this folder (default: next to each STEP file) |
| `-q, --quality {draft,normal,fine}` | Mesh quality preset (default: `normal`) |
| `-d, --deflection MM` | Absolute mesh tolerance in model units (mm); overrides `--quality` |
| `-r, --recursive` | Scan folders recursively |
| `--skip-existing` | Skip files whose GLB already exists |
| `--z-up` | Keep the STEP Z-up axis instead of converting to glTF Y-up |
| `--mm` | Keep millimetres instead of converting to metres |
| `--version` | Print the version |

The exit code is `0` when every file converted, `1` if at least one failed, `2` if no STEP file was found.

## Troubleshooting

### Windows

- **"Windows protected your PC" (SmartScreen).** The exe is not code-signed. Click *More info*,
  then *Run anyway*. If the zip was downloaded from the internet, right-click it, open
  *Properties* and tick *Unblock* before extracting.
- **The exe is blocked by your IT policy.** Some company setups only allow signed or approved
  programs. In that case ask IT to allow the extracted folder, or run it from a location where
  executables are permitted.
### macOS says the app can't be opened

The app is not signed or notarized by Apple (that requires a paid Apple Developer account), so
macOS blocks it the first time with a message like *"STEP2GLB" can't be opened because Apple
cannot check it for malicious software* or *"STEP2GLB" Not Opened*. You only need to allow it once:

- **macOS 15 Sequoia and newer:** try to open the app and close the message. Then open
  *System Settings → Privacy & Security*, scroll down to the message about STEP2GLB, click
  **Open Anyway**, and confirm with your password.
- **macOS 14 Sonoma and older:** right-click (or Control-click) `STEP2GLB.app`, choose **Open**,
  then **Open** again in the dialog.
- **If it still refuses** (for example *"STEP2GLB is damaged and can't be opened"*), remove the
  download quarantine flag from Terminal, then open it normally:

  ```
  xattr -dr com.apple.quarantine /Applications/STEP2GLB.app
  ```

  (Use the path where you put the app.)

On a company Mac managed by IT, these options may be disabled: ask IT to allow the app.

### Any system

- **"OpenCASCADE could not read this file".** The file is not a valid STEP file, or it is
  truncated. STEP AP203, AP214 and AP242 are the usual formats.
- **Very large files.** Conversion needs a lot of memory. Use a 64-bit Windows, close other
  applications, and try the **Draft** preset.

## Build from source

The Windows and macOS builds are produced by GitHub Actions (see `.github/workflows/build.yml`):
every push builds the app on both systems, runs the tests, converts a generated sample with the
built command line tool, checks that the main program is the window, and uploads the zips.
Pushing a tag such as `v1.1.0` also publishes both zips as a release.

To run from source (Python 3.12):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest
python -m step2glb                 # opens the window
python -m step2glb model.step -q draft   # options switch to command-line mode
python -m PyInstaller --noconfirm --clean STEP2GLB.spec   # dist\STEP2GLB (and dist/STEP2GLB.app on macOS)
```

## License

MIT, see [LICENSE](LICENSE). The converter uses OpenCASCADE Technology (LGPL 2.1 with an
exception) through the [`cadquery-ocp`](https://github.com/CadQuery/OCP) Python bindings
(Apache 2.0). Drag and drop uses [tkdnd](https://github.com/petasis/tkdnd) through
[`tkinterdnd2`](https://github.com/Eliav2/tkinterdnd2) (MIT).
