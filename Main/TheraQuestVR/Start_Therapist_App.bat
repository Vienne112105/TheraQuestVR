@echo off
title TheraQuest VR - Therapist Command Center
rem Runs the built program (server\build_app.py) when it exists; otherwise runs app.py with Python.
set "APP=%~dp0server\dist\TheraQuest Therapist\TheraQuest Therapist.exe"
if exist "%APP%" (
  start "" "%APP%"
  exit /b 0
)
cd /d "%~dp0server"
python app.py
if errorlevel 1 pause
