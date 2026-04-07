# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

project_root = Path(os.environ.get('PROJECT_ROOT', '/Users/azm/MyProject/xhs-comments-reply2'))
dist_backend = project_root / "dist_backend"

a = Analysis(
    [str(project_root / "packager" / "boot.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(dist_backend / "app"), "app"),
        (str(dist_backend / "pyarmor_runtime_000000"), "pyarmor_runtime_000000"),
        (str(dist_backend / "prompts"), "prompts"),
        (str(dist_backend / "config.py"), "."),
        (str(project_root / "backend" / "static"), "static"),
        (str(project_root / "config.json"), "."),
    ],
    hiddenimports=[
        "flask", "flask_cors", "requests", "websockets", "apscheduler",
        "python_dotenv", "dotenv", "json", "yaml", "pathlib",
        "openai", "aiohttp", "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="XHSCommentApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="XHSCommentApp",
    info_plist={
        "CFBundleName": "XHSCommentApp",
        "CFBundleDisplayName": "小红书评论助手",
        "CFBundleIdentifier": "com.xhs.commentapp",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "XHSCommentApp",
        "LSMinimumSystemVersion": "10.13",
    },
)
