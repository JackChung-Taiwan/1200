@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto python
start "" http://localhost:8000
py -3 -m http.server 8000 --directory dist
goto end
:python
where python >nul 2>nul
if errorlevel 1 goto missing
start "" http://localhost:8000
python -m http.server 8000 --directory dist
goto end
:missing
echo Python 3 is not installed. Please open dist/index.html directly.
:end
pause
