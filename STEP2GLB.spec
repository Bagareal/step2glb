# PyInstaller spec: builds a portable folder dist/STEP2GLB/ containing
#   STEP2GLB.exe       - the window (no console, like any normal Windows app)
#   step2glb-cli.exe   - the command line version (console)
# Both share the same libraries in the folder.
# Usage: pyinstaller --noconfirm --clean STEP2GLB.spec
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("OCP")
tk_imports = ["tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox"]

gui = Analysis(
    ["app.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + tk_imports,
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
