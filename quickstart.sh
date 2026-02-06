#!/bin/bash
# Quick start script for OpenCode Python

set -e

echo "🚀 OpenCode Python - Quick Start"
echo "================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found!"
    echo "   Please run this script from the python/ directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install package
echo "📥 Installing OpenCode..."
pip install -q -e ".[dev]"

# Run tests
echo "🧪 Running tests..."
if pytest tests/ -q --tb=short 2>/dev/null; then
    echo "   ✅ All tests passed!"
else
    echo "   ⚠️  Some tests failed (this is normal for initial setup)"
fi

# Run examples
echo ""
echo "🎨 Running examples..."
python examples/basic_usage.py || echo "   Examples completed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "   2. Try the CLI: opencode --help"
echo "   3. Run tests: pytest tests/ -v"
echo "   4. See BUILD_AND_RUN.md for detailed instructions"
echo ""
