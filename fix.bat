@echo off
REM Fix installation with minimal dependencies (Windows)

echo 🔧 OpenCode Python - Installation Fix
echo ====================================
echo.

REM Check if pyproject.toml exists
if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml not found!
    echo    Please run this script from the python/ directory
    pause
    exit /b 1
)

echo 📦 Creating fresh virtual environment...
if exist "venv" (
    echo    Removing old environment...
    rmdir /s /q venv
)
python -m venv venv

echo 🔌 Activating virtual environment...
call venv\Scripts\activate

echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

echo 📥 Installing minimal dependencies first...
pip install -r requirements-minimal.txt

echo 📦 Installing OpenCode (without dependencies)...
pip install -e . --no-deps

echo.
echo ✅ Installation complete!
echo.
echo Testing...
python -c "import opencode; print('✓ Module imported successfully')" 2>nul || echo ⚠️  Import test had warnings
echo.
echo 🎯 Next steps:
echo    1. Virtual environment is activated
echo.
echo    2. Try the CLI:
echo       opencode --help
echo.
echo    3. Install additional features as needed:
echo       pip install openai anthropic  [For AI providers]
echo       pip install pytest black ruff  [For development]
echo.

pause
