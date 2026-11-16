# PyInstaller spec: builds a portable folder dist/STEP2GLB/ containing STEP2GLB.exe
# Usage: pyinstaller --noconfirm --clean STEP2GLB.spec
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("OCP")

a = Analysis(
    ["app.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + ["tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="STEP2GLB",
    console=True,  # GUI mode hides the console itself; --options mode needs it
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="STEP2GLB", upx=False)
