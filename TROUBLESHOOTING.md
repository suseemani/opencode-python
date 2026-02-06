# Troubleshooting Installation Issues

## ❌ pip install -e . fails

### Common Causes and Solutions

#### 1. **Wrong Directory**
**Error:** `ERROR: File "setup.py" or "setup.cfg" not found`

**Solution:** Make sure you're in the `python/` directory:
```bash
cd python  # Must be in the python directory
pip install -e .
```

#### 2. **Missing Build Tools**
**Error:** `ERROR: Could not build wheels for ...`

**Solution:** Install build dependencies first:
```bash
pip install --upgrade pip setuptools wheel hatchling
pip install -e .
```

#### 3. **Python Version**
**Error:** `Package 'opencode' requires a different Python version`

**Solution:** Check your Python version (requires 3.11+):
```bash
python --version  # Should be 3.11 or higher
```

If using an older version, install Python 3.11 or higher.

#### 4. **Virtual Environment Issues**
**Error:** Various permission or path errors

**Solution:** Always use a virtual environment:
```bash
# Create fresh virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install
pip install -e .
```

#### 5. **Dependency Conflicts**
**Error:** `ERROR: Cannot install opencode because these package versions have conflicting dependencies`

**Solution:** Install in a clean environment:
```bash
# Remove old environment
rm -rf venv  # Linux/macOS
rmdir /s /q venv  # Windows

# Create fresh one
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Upgrade pip and install
pip install --upgrade pip
pip install -e .
```

### ✅ Complete Working Setup

If you're still having issues, try this complete setup:

**Step 1: Navigate to correct directory**
```bash
cd C:\Users\susee\repos\opencode\python
```

**Step 2: Create fresh virtual environment**
```bash
python -m venv venv
```

**Step 3: Activate it**
```bash
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

**Step 4: Upgrade pip and install build tools**
```bash
python -m pip install --upgrade pip setuptools wheel hatchling
```

**Step 5: Install the package**
```bash
pip install -e .
```

### 🔍 Debug Installation

To see detailed error messages:
```bash
pip install -e . -v  # Verbose output
```

### 🆘 Still Not Working?

Try installing dependencies first, then the package:
```bash
# Install dependencies manually
pip install pydantic>=2.0.0 typer>=0.12.0 fastapi>=0.109.0 httpx>=0.27.0

# Then install without deps
pip install -e . --no-deps
```

### 📋 Verify Installation

After successful installation:
```bash
# Check CLI
opencode --help

# Check module
python -c "import opencode; print('Success!')"

# Run tests
pytest tests/ -v
```

### 🐛 Specific Error Messages

#### `ModuleNotFoundError: No module named 'opencode'`
- Virtual environment not activated
- Package not installed: run `pip install -e .`

#### `ImportError: cannot import name '...' from 'opencode'`
- Partial installation
- Solution: `pip uninstall opencode && pip install -e .`

#### `Permission denied`
- Don't use sudo with pip
- Solution: Use virtual environment

### 📞 Getting Help

If none of these solutions work:
1. Check Python version: `python --version` (need 3.11+)
2. Check pip version: `pip --version`
3. Run with verbose flag: `pip install -e . -v`
4. Share the full error message

## 🎯 Quick Fix Script

Run this script to fix most issues:

**Windows (fix.bat):**
```batch
@echo off
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel hatchling
pip install -e .
echo Done!
```

**Linux/macOS (fix.sh):**
```bash
#!/bin/bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel hatchling
pip install -e .
echo "Done!"
```
