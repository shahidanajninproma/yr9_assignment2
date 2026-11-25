@echo off
REM One-click launcher (Windows). Double-click this file.
REM First run: creates a private .venv and installs requirements (needs internet). Later runs start in seconds.
setlocal
cd /d "%~dp0"
title Dutch offshore wind dashboard

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo Python 3.10 or newer was not found.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH", then run this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment ...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)

echo Checking packages ...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fail

echo Starting dashboard. Your browser will open; close this window to stop it.
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo Something went wrong (see messages above). Check your internet connection and try again.
pause
exit /b 1
