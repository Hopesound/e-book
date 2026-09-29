@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Please install Node.js LTS first: https://nodejs.org/
  pause
  exit /b 1
)
if not exist "node_modules\vite" (
  call npm.cmd install
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
echo Opening Onleaf at http://127.0.0.1:5173
call npm.cmd run dev -- --open
pause
