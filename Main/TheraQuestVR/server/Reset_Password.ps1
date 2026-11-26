# Reset the clinician password on the REAL database (%LOCALAPPDATA%\TheraQuest\theraquest.db).
# Why a wrapper: the Microsoft Store build of Python is sandboxed. It silently redirects writes under
# %LOCALAPPDATA% to a private copy, so running reset_password.py directly changes the wrong file.
# This script copies the database outside that folder, resets the password there, and copies it back.
#
# Usage (PowerShell, from this folder, Therapist app closed):   .\Reset_Password.ps1 [username]
param([string]$Username = "")

$ErrorActionPreference = "Stop"
$real = Join-Path $env:LOCALAPPDATA "TheraQuest\theraquest.db"
$work = Join-Path $env:USERPROFILE "TheraQuestReset"

if (-not (Test-Path $real)) { throw "Database not found: $real" }
if (Get-Process -Name "TheraQuest Therapist" -ErrorAction SilentlyContinue) {
    throw "Close the TheraQuest Therapist app first (check Task Manager), then run this again."
}
foreach ($ext in "-wal", "-shm") {
    if (Test-Path ($real + $ext)) { throw "Found $($real + $ext): the database is still in use. Close the app and try again." }
}

New-Item -ItemType Directory -Force $work | Out-Null
$copy = Join-Path $work "theraquest.db"
Remove-Item "$copy*" -Force -ErrorAction SilentlyContinue
Copy-Item $real $copy

$env:THERAQUEST_DB = $copy
Push-Location $PSScriptRoot
try {
    if ($Username) { python reset_password.py $Username } else { python reset_password.py }
    if ($LASTEXITCODE -ne 0) { throw "Password was not changed (see message above). The real database was not touched." }
} finally { Pop-Location }

# Make sure SQLite has written everything into the main file, then swap it in (old file kept as a backup).
python -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('PRAGMA wal_checkpoint(TRUNCATE)'); c.close()" $copy
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $real "$real.before-reset-$stamp"
Copy-Item $copy $real -Force
Remove-Item "$copy*" -Force -ErrorAction SilentlyContinue
Write-Host "Done. The real database now has the new password. Backup of the old file: $real.before-reset-$stamp"
