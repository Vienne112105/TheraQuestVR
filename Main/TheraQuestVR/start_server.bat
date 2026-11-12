@echo off
title TheraQuest server
rem Backend only (for Unity, development and tests). Therapists use Start_Therapist_App.bat (DEC-013).
cd /d "%~dp0server"
python server.py
pause
