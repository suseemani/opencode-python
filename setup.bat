@echo off
REM Quick start script for OpenCode Python (Windows)

echo 🚀 OpenCode Python - Quick Start
echo =================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml not found!
    echo    Please run this script from the python/ directory
    pause
    exit /b 1
)

REM Check Python version
echo 📋 Checking Python version...
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo ⬆️  Upgrading pip...
pip install --upgrade pip -q

REM Install package
echo 📥 Installing OpenCode package...
pip install -q -e "."

echo.
echo ✅ Installation complete!
echo.
echo 🎯 Next steps:
echo    1. Virtual environment is activated
echo.
echo    2. Try the CLI:
echo       opencode --help
echo.
echo    3. Run tests:
echo       pytest tests/ -v
echo.
echo    4. Run examples:
echo       python examples/basic_usage.py
echo.
echo 📚 See BUILD_AND_RUN.md for detailed instructions
echo.

pause
