# PyInstaller onedir build. Run on the target OS; this is not cross-compilation.
import json
import sys
from pathlib import Path

root = Path(SPECPATH)
required = json.loads((root / "packaging/resources.json").read_text(encoding="utf-8"))
for relative in required:
    if not (root / relative).is_file():
        raise SystemExit(f"Missing required ClockIn resource: {relative}")

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / folder), folder) for folder in ("assets", "styles", "defaults")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
# PyInstaller's PySide6 hooks collect the imported Qt modules and their plugins.
# No collect-all, manual Qt DLL copies, or speculative hidden imports are needed.
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ClockIn",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / "assets/logo.ico") if sys.platform == "win32" else None,
    contents_directory=".",
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="ClockIn")
