# Checking Python Version

## For Your Local OpenCode Installation

### Method 1: Check Virtual Environment Python

**Windows:**
```cmd
cd python
venv\Scripts\python --version
```

**Linux/macOS:**
```bash
cd python
venv/bin/python --version
```

### Method 2: Activate and Check

**Windows:**
```cmd
cd python
venv\Scripts\activate
python --version
```

**Linux/macOS:**
```bash
cd python
source venv/bin/activate
python --version
```

### Method 3: Check Inside Python

```bash
cd python
venv\Scripts\python -c "import sys; print(f'Python {sys.version}')"
```

## Check All Python Versions on System

**Windows:**
```cmd
where python
python --version
```

**Linux/macOS:**
```bash
which python
python3 --version
```

## Verify OpenCode Requirements

OpenCode requires **Python 3.11 or higher**.

To check if your Python version is compatible:

```bash
cd python

# Check version
python --version

# Check if meets requirement (3.11+)
python -c "import sys; print('✓ Compatible' if sys.version_info >= (3, 11) else '✗ Need Python 3.11+')"
```

## Common Issue: Wrong Python Version

If your system has multiple Python versions, you might need to specify:

```bash
# Use python3 explicitly
cd python
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
python3 --version

# Or specify full path
/path/to/python3.11 -m venv venv
```

## Quick Diagnostic Script

Save this as `check_python.bat` (Windows) or `check_python.sh` (Linux/macOS):

**Windows (`check_python.bat`):**
```batch
@echo off
echo Checking Python versions...
echo.
echo System Python:
python --version 2>nul || echo Not found
echo.
echo Python3:
python3 --version 2>nul || echo Not found
echo.
if exist "venv\Scripts\python.exe" (
    echo Virtual Environment Python:
    venv\Scripts\python --version
) else (
    echo No virtual environment found
)
echo.
pause
```

**Linux/macOS (`check_python.sh`):**
```bash
#!/bin/bash
echo "Checking Python versions..."
echo ""
echo "System Python:"
python --version 2>/dev/null || echo "Not found"
echo ""
echo "Python3:"
python3 --version 2>/dev/null || echo "Not found"
echo ""
if [ -f "venv/bin/python" ]; then
    echo "Virtual Environment Python:"
    venv/bin/python --version
else
    echo "No virtual environment found"
fi
```

Run it:
```bash
cd python
./check_python.sh      # Linux/macOS
check_python.bat       # Windows
```

## Next Steps

If your Python version is **below 3.11**:
1. Install Python 3.11 or higher from [python.org](https://python.org)
2. Create a new virtual environment with the new version
3. Reinstall opencode

If your Python version is **3.11 or higher**:
1. Proceed with installation: `pip install -e .`
