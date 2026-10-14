@echo off
rem Try the newest Knightwise straight from this folder, before it goes to the Store.
rem   try          with your own games (the project's data folder)
rem   try fresh    as a brand-new player: the welcome screen, nothing kept afterwards
rem Only one Knightwise can run at a time, so this first closes the Store copy (start it again from the Start menu).
cd /d "%~dp0"
taskkill /im Knightwise.exe /f >nul 2>&1
taskkill /im ChessCoach.exe /f >nul 2>&1
set KNIGHTWISE_HOME=
if /i "%~1"=="fresh" (
  set "KNIGHTWISE_HOME=%TEMP%\knightwise-try"
  if exist "%TEMP%\knightwise-try" rmdir /s /q "%TEMP%\knightwise-try"
)
rem No console window: closing a black window used to close Knightwise too (13 Oct test). Errors go to the logbook.
start "" pythonw -m coach.app
