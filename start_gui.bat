@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo             iDotMatrix Controller Launcher
echo ========================================================

set "PY_EXE="
if exist ".\venv_windows\Scripts\python.exe" (
    set "PY_EXE=.\venv_windows\Scripts\python.exe"
) else if exist ".\venv\Scripts\python.exe" (
    set "PY_EXE=.\venv\Scripts\python.exe"
)

if "%PY_EXE%"=="" (
    echo Virtual environment not found. Attempting to create one...
    python -m venv venv_windows
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        echo Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    set "PY_EXE=.\venv_windows\Scripts\python.exe"
    echo Installing dependencies from requirements.txt...
    "%PY_EXE%" -m pip install --upgrade pip
    "%PY_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting iDotMatrix GUI...
"%PY_EXE%" gui.py
if errorlevel 1 (
    echo.
    echo [ERROR] The application stopped unexpectedly with exit code %errorlevel%.
    pause
)

endlocal
