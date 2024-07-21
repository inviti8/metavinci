# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/media/desktop/HD2/Dev/hvym-daemon/build/metavinci.py'],
    pathex=[],
    binaries=[],
    datas=[('images', 'images'), ('data', 'data'), ('service', 'service')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='metavinci',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/media/desktop/HD2/Dev/hvym-daemon/hvym_logo_64.ico'],
)
