#!/bin/bash
# Quick start script for OpenCode Python

echo "🚀 OpenCode Python - Quick Start"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found!"
    echo "   Please run this script from the python/ directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 || python --version 2>&1)
echo "   Found: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv 2>/dev/null || python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install package
echo "📥 Installing OpenCode package..."
pip install -q -e "."

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Activate virtual environment (if not already active):"
echo "      source venv/bin/activate  # Linux/macOS"
echo "      venv\\Scripts\\activate    # Windows"
echo ""
echo "   2. Try the CLI:"
echo "      opencode --help"
echo ""
echo "   3. Run tests:"
echo "      pytest tests/ -v"
echo ""
echo "   4. Run examples:"
echo "      python examples/basic_usage.py"
echo ""
echo "📚 See BUILD_AND_RUN.md for detailed instructions"
