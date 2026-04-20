# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

project_root = Path.cwd()
datas = [
    (str(project_root / "src" / "reporting" / "streamlit_app.py"), "src/reporting"),
]
binaries = []
hiddenimports = []

for package_name in ("streamlit", "pandas", "numpy", "altair", "pydeck", "tornado"):
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception:
        pass

a = Analysis(
    [str(project_root / "src" / "reporting" / "dashboard_launcher.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SalesDashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="SalesDashboard",
)
