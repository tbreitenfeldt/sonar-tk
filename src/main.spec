# -*- mode: python ; coding: utf-8 -*-

import os
import platform

block_cipher = None
binaries = []

if platform.system() == "Windows":
    binaries = [(os.path.join('accessible_output2', 'lib', 'nvdaControllerClient32.dll'), '.'), (os.path.join('accessible_output2', 'lib', 'nvdaControllerClient64.dll'), '.'),
                (os.path.join('accessible_output2', 'lib', 'dolapi.dll'), '.'), (os.path.join('accessible_output2', 'lib', 'PCTKUSR.dll'), '.'), (os.path.join('accessible_output2', 'lib', 'PCTKUSR64.dll'), '.'),
                (os.path.join('accessible_output2', 'lib', 'SAAPI32.dll'), '.')]

a = Analysis(['main.py'],
             pathex=[SPECPATH],
             binaries= binaries,
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
