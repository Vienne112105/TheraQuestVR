@echo off
title TheraQuest VR - Encrypted database backup
cd /d "%~dp0\server"
echo Writes an encrypted copy of the patient database (for example to a USB drive).
echo You will choose a password. A lost password means the backup cannot be opened.
set /p DEST=Folder to save the backup in (e.g. E:\TheraQuestBackups): 
if "%DEST%"=="" exit /b 1
python backup.py backup "%DEST%"
pause
