@echo off
title TheraQuest VR - Therapist Command Center
cd /d "%~dp0\server"
python app.py
if errorlevel 1 (
    echo.
    echo Fallback: Opening dedicated application window...
    start msedge.exe --app=http://localhost:8000 --window-size=1360,880
)
