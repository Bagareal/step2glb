# PyInstaller spec. Builds a portable folder dist/STEP2GLB/ containing
#   STEP2GLB(.exe)       - the window (no console, like any normal app)
#   step2glb-cli(.exe)   - the command line version (console)
# On macOS it also wraps them into dist/STEP2GLB.app.
# Usage: pyinstaller --noconfirm --clean STEP2GLB.spec
import re
import sys

from PyInstaller.utils.hooks import collect_all

version = re.search(r'__version__ = "([^"]+)"', open("src/step2glb/__init__.py").read()).group(1)

datas, binaries, hiddenimports = collect_all("OCP")
dnd_datas, dnd_binaries, dnd_hidden = collect_all("tkinterdnd2")
tk_imports = ["tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox", "tkinter.font"]

gui = Analysis(
    ["app.py"],
    pathex=["src"],
    binaries=binaries + dnd_binaries,
    datas=datas + dnd_datas,
    hiddenimports=hiddenimports + dnd_hidden + tk_imports,
    noarchive=False,
)
cli = Analysis(
    ["cli_app.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)

# The GUI exe must come first: on macOS the first executable becomes the .app's main program.
gui_exe = EXE(
    PYZ(gui.pure),
    gui.scripts,
    [],
    exclude_binaries=True,
    name="STEP2GLB",
    console=False,
    upx=False,
)
cli_exe = EXE(
    PYZ(cli.pure),
    cli.scripts,
    [],
    exclude_binaries=True,
    name="step2glb-cli",
    console=True,
    upx=False,
)

coll = COLLECT(
    gui_exe,
    cli_exe,
    gui.binaries,
    gui.datas,
    cli.binaries,
    cli.datas,
    name="STEP2GLB",
    upx=False,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="STEP2GLB.app",
        bundle_identifier="io.github.bagareal.step2glb",
        version=version,
        info_plist={
            "CFBundleName": "STEP2GLB",
            "CFBundleDisplayName": "STEP to GLB",
            "CFBundleShortVersionString": version,
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "STEP CAD file",
                "CFBundleTypeExtensions": ["step", "stp", "STEP", "STP"],
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
            }],
        },
    )
