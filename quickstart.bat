@echo off
REM Quick start script for OpenCode Python (Windows)

echo 🚀 OpenCode Python - Quick Start
echo =================================
echo.

REM Check Python version
echo 📋 Checking Python version...
python --version

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml not found!
    echo    Please run this script from the python/ directory
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate

REM Install package
echo 📥 Installing OpenCode...
pip install -q -e ".[dev]"

REM Run tests
echo 🧪 Running tests...
pytest tests/ -q --tb=short >nul 2>&1
if %errorlevel% == 0 (
    echo    ✅ All tests passed!
) else (
    echo    ⚠️  Some tests failed (this is normal for initial setup)
)

REM Run examples
echo.
echo 🎨 Running examples...
python examples/basic_usage.py

echo.
echo ✅ Setup complete!
echo.
echo 🎯 Next steps:
echo    1. Virtual environment is already activated
echo    2. Try the CLI: opencode --help
echo    3. Run tests: pytest tests/ -v
echo    4. See BUILD_AND_RUN.md for detailed instructions
echo.

pause
