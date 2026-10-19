@echo off
title TheraQuest VR - Therapist Command Center
cd /d "%~dp0\server"
python app.py
if errorlevel 1 pause
