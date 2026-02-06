# Build and Run Steps for OpenCode Python

## ⚡ Quick Setup (Automated)

### Option 1: Run Setup Script

**Linux/macOS:**
```bash
cd python
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
cd python
setup.bat
```

### Option 2: Manual Setup

**Step 1: Navigate to python directory**
```bash
cd python
```

**Step 2: Create virtual environment**
```bash
python -m venv venv
```

**Step 3: Activate virtual environment**

Linux/macOS:
```bash
source venv/bin/activate
```

Windows:
```cmd
venv\Scripts\activate
```

**Step 4: Install package**
```bash
pip install -e .
```

## 🚀 Running the Application

### Run CLI
```bash
opencode --help
```

### Run Tests
```bash
pytest tests/ -v
```

### Run Examples
```bash
python examples/basic_usage.py
```

### Run Server
```bash
python -c "from opencode.server import Server; s = Server(); s.run()"
```

## 📝 Common Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Format code
black opencode/ tests/

# Run linter
ruff check opencode/ tests/

# Type check
mypy opencode/

# Build for distribution
pip install build
python -m build
```

## ✅ Requirements

- Python 3.11+
- pip
- Virtual environment (recommended)

## 🐛 Troubleshooting

**Issue: Module not found**
- Solution: Make sure virtual environment is activated

**Issue: Permission denied**
- Solution: Use `sudo` on Linux/macOS or run as Administrator on Windows

**Issue: Tests fail**
- Solution: Some tests may require external dependencies. Check test output for details.

## 📚 More Info

See BUILD_AND_RUN.md for complete documentation.
