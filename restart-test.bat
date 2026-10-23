@echo off
rem Restart the Knightwise test copy (the one from "try test"): closes it, then starts it again.
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -match 'coach.app|multiprocessing' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
start "" cmd /c "%~dp0try.bat" test
