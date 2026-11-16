# STEP2GLB

Portable **STEP / STP to GLB** converter for Windows. No installation, no Python, no admin rights:
download a zip, extract it anywhere, run `STEP2GLB.exe`.

It is built on [OpenCASCADE](https://dev.opencascade.org/) (the same CAD kernel used by FreeCAD)
and is meant for large CAD files that are too heavy to open directly in a browser-based 3D viewer.

## Quick start

1. Download `STEP2GLB-windows-x64.zip` from the [Releases](../../releases) page and extract it
   (a USB stick or any folder you can write to is fine).
2. Run `STEP2GLB.exe`, then either:
   - **drag one or more `.step` / `.stp` files (or a folder) onto `STEP2GLB.exe`**, or
   - double-click it, click **Add files...** or **Add folder...**, then **Convert to GLB**.
3. The `.glb` files appear next to the STEP files (or in the output folder you chose).

Large files can take a while. The window shows progress for each file, and several files are
converted one after the other.

## What is kept in the GLB

| Kept | Notes |
| --- | --- |
| Assembly hierarchy | Parts and sub-assemblies stay separate nodes, so you can select or hide them individually |
| Part names | Product name first, instance name as a fallback |
| Colours | As defined in the STEP file |
| Repeated parts | A part used many times is stored once and instanced, which keeps files small |
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
`step2glb-cli.exe`, which is in the same folder. Run it from a terminal:

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

- **"Windows protected your PC" (SmartScreen).** The exe is not code-signed. Click *More info*,
  then *Run anyway*. If the zip was downloaded from the internet, right-click it, open
  *Properties* and tick *Unblock* before extracting.
- **The exe is blocked by your IT policy.** Some company setups only allow signed or approved
  programs. In that case ask IT to allow the extracted folder, or run it from a location where
  executables are permitted.
- **"OpenCASCADE could not read this file".** The file is not a valid STEP file, or it is
  truncated. STEP AP203, AP214 and AP242 are the usual formats.
- **Very large files.** Conversion needs a lot of memory. Use a 64-bit Windows, close other
  applications, and try the **Draft** preset.

## Build from source

The Windows build is produced by GitHub Actions (see `.github/workflows/build.yml`): every push
builds the app, runs the tests, converts a generated sample with the built `step2glb-cli.exe`,
checks that `STEP2GLB.exe` is a windowed app, and uploads a zip.
Pushing a tag such as `v1.0.0` also publishes it as a release.

To run from source (Python 3.12):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest
python -m step2glb                 # opens the window
python -m step2glb model.step -q draft   # options switch to command-line mode
python -m PyInstaller --noconfirm --clean STEP2GLB.spec   # portable build in dist\STEP2GLB
```

## License

MIT, see [LICENSE](LICENSE). The converter uses OpenCASCADE Technology (LGPL 2.1 with an
exception) through the [`cadquery-ocp`](https://github.com/CadQuery/OCP) Python bindings
(Apache 2.0).
