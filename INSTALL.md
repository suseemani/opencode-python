# OpenCode Python - Installation Guide

## ⚠️ Important: Fixing Dependency Issues

If you encounter `No matching distribution found` errors, use the minimal requirements first:

### Quick Fix (Minimal Install)

```bash
cd python

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install minimal dependencies first
pip install -r requirements-minimal.txt

# Then install the package without deps
pip install -e . --no-deps

# Install other dependencies as needed
pip install aiofiles pyyaml gitpython fuzzywuzzy
```

### Removed Dependencies

The following dependencies have been removed from pyproject.toml:
- `bonjour-py>=0.3.0` - Package not available on PyPI

### Alternative: Skip Problematic Packages

If other packages fail:

```bash
# Install core dependencies only
pip install pydantic>=2.0.0 httpx>=0.27.0 fastapi>=0.109.0 uvicorn>=0.27.0 typer>=0.12.0 rich>=13.7.0 python-dotenv>=1.0.0

# Then install opencode
pip install -e . --no-deps
```

## 🐛 Common Installation Issues

### Issue: No matching distribution found for X

**Solution:** Skip that package and install without it:
```bash
pip install -e . --no-deps
# Then manually install working dependencies
```

### Issue: Package conflicts

**Solution:** Use fresh virtual environment:
```bash
rm -rf venv  # or rmdir /s /q venv on Windows
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-minimal.txt
pip install -e . --no-deps
```

## ✅ Verification After Install

```bash
# Test import
python -c "import opencode; print('✓ Success!')"

# Test CLI
opencode --help
```

## 📦 Full Dependencies (Optional)

After basic install works, you can add more features:

```bash
# For AI providers
pip install openai anthropic

# For development tools
pip install pytest black ruff mypy

# For advanced features
pip install websockets aiofiles pyyaml gitpython
```
