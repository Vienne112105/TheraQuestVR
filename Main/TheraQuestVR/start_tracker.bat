@echo off
title TheraQuest tracker
cd /d "%~dp0tracker"

rem MediaPipe needs Python 3.11 or 3.12
python -c "import sys; sys.exit(0 if sys.version_info[:2] in ((3,11),(3,12)) else 1)"
if errorlevel 1 (
  echo This tracker needs Python 3.11 or 3.12. Found:
  python --version
  pause
  exit /b 1
)

rem .venv\installed.ok is written only after a successful install, so a failed install is retried
if not exist .venv\Scripts\python.exe python -m venv .venv
if not exist .venv\installed.ok (
  echo Installing tracker packages, first run only...
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Package install failed. Check your internet connection and run this again.
    pause
    exit /b 1
  )
  echo ok> .venv\installed.ok
)

.venv\Scripts\python.exe tracker.py %*
pause
