"""
PyInstaller spec file generator for PyTorrent
Run this to create the .spec file for building
"""

import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create the spec file content
spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{os.path.join(current_dir, "main.py")}'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[
        ('{os.path.join(current_dir, "icon.svg")}', '.'),
        ('{os.path.join(current_dir, "README.md")}', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'libtorrent',
        'bencode',
        'requests',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyTorrent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # No icon for executable
)

# For macOS, create an app bundle
import platform
if platform.system() == 'Darwin':
    app = BUNDLE(
        exe,
        name='PyTorrent.app',
        icon=None,  # No icon for app bundle
        bundle_identifier='com.pytorrent.app',
        info_plist={{
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {{
                    'CFBundleTypeName': 'Torrent File',
                    'CFBundleTypeExtensions': ['torrent'],
                    'CFBundleTypeRole': 'Editor',
                }}
            ]
        }},
    )
'''

# Write the spec file
with open(os.path.join(current_dir, 'PyTorrent.spec'), 'w') as f:
    f.write(spec_content)

print("Created PyTorrent.spec file successfully!")
print("Next steps:")
print("1. Install PyInstaller: pip install pyinstaller")
print("2. Run: pyinstaller PyTorrent.spec")