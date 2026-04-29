# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['gui\\GUI__isd_str_sdk.py'],
    pathex=[SPECPATH, os.path.join(SPECPATH, 'src')],
    binaries=[],
    datas=[
        ('gui/sample_matching.csv', 'gui'),
        (
            'src/isd_str_sdk/str_cleaning/strategies/pre_contexted/權控分析_資料前處理_統一詞彙用權控表.xlsx',
            'isd_str_sdk/str_cleaning/strategies/pre_contexted',
        ),
    ],
    hiddenimports=[
        'gui._shared',
        'gui._tab_cleaning',
        'gui._tab_matching',
        'gui._tab_tdd',
        'gui._tab_result_helper',
        'isd_str_sdk.str_cleaning',
        'isd_str_sdk.base.StrProcessorsChain',
        'isd_str_sdk.str_matching',
        'isd_str_sdk.str_matching.adapters',
        'isd_str_sdk.TDD.run_strategy_tests',
        'isd_str_sdk.core.contexts',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['sentence_transformers', 'torch', 'transformers', 'tokenizers', 'huggingface_hub', 'safetensors', 'wheel'],
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
    name='GUI__isd_str_sdk',
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
)
