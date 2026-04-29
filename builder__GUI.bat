@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION

echo =========================================
echo 確認你正在 venv 環境下執行此腳本
echo =========================================
set /p CONFIRM="你確定是在虛擬環境下嗎？ (y/n): "

if /I "%CONFIRM%"=="y" (
    echo Detecting python executable...
    if defined VIRTUAL_ENV (
        set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
    ) else (
        set "PYTHON_EXE=python"
    )
    echo Using python: !PYTHON_EXE!

    echo 正在升級 pip, build, setuptools, wheel...
    "!PYTHON_EXE!" -m pip install --upgrade pip
    "!PYTHON_EXE!" -m pip install --upgrade build setuptools wheel
    "!PYTHON_EXE!" -m PyInstaller .\GUI__isd_str_sdk.spec

    echo 完成！
) else (
    echo 已取消執行。請先啟動你的 venv。
)

ENDLOCAL
pause
