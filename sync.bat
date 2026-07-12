@echo off
echo Starting LeetCode Sync...

:: Set encoding to UTF-8 to prevent emoji crashes on Windows
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Navigate to the script directory (just in case it's run from somewhere else)
cd /d "%~dp0"

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Run the script in sync mode
python main.py --sync

:: Deactivate when done
call deactivate

echo.
echo Sync Complete!
pause
