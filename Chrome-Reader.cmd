@echo off
setlocal
where node >nul 2>nul
if errorlevel 1 (
  echo Please install Node.js LTS first: https://nodejs.org/
  pause
  exit /b 1
)
node "%~dp0tools\speech-relay\launch.cjs"
if errorlevel 1 pause
