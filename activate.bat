@echo off
REM Quick activation script for virtual environment
REM Double-click this file to activate the venv in a new command prompt

echo =========================================
echo Schwab Trading Agent Tools
echo =========================================
echo.
echo Activating virtual environment...
echo.

if not exist venv\ (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo =========================================
echo Virtual environment activated!
echo =========================================
echo.
echo Your prompt should now show: (venv)
echo.
echo Quick commands:
echo   - Run Weather Agent:  python Weather_Tools\weather_tools.py --symbol ES --output pretty
echo   - Test installation:  python test_installation.py
echo   - Deactivate venv:    deactivate
echo.
echo =========================================

cmd /k
