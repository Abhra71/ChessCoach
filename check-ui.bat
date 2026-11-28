@echo off
rem The UI department: opens every page of Knightwise in a hidden, muted Edge and checks it (tests/ui/test_pages.py).
rem Screenshots of every page land in logbook\ui-check\. Uses a private copy of the app on port 8799; the Store app and
rem your own data are never touched.
cd /d "%~dp0"
set KNIGHTWISE_UI=1
python -m pytest tests/ui -q -p no:cacheprovider %*
