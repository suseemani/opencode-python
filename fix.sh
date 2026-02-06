#!/bin/bash
# Fix installation with minimal dependencies

set -e

echo "🔧 OpenCode Python - Installation Fix"
echo "===================================="
echo ""

cd "$(dirname "$0")"

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found!"
    echo "   Please run this script from the python/ directory"
    exit 1
fi

echo "📦 Creating fresh virtual environment..."
if [ -d "venv" ]; then
    echo "   Removing old environment..."
    rm -rf venv
fi
python3 -m venv venv 2>/dev/null || python -m venv venv

echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

echo "📥 Installing minimal dependencies first..."
pip install -r requirements-minimal.txt

echo "📦 Installing OpenCode (without dependencies)..."
pip install -e . --no-deps

echo ""
echo "✅ Installation complete!"
echo ""
echo "Testing..."
python -c "import opencode; print('✓ Module imported successfully')" || echo "⚠️  Import test failed"

echo ""
echo "🎯 Next steps:"
echo "   1. Activate virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Try the CLI:"
echo "      opencode --help"
echo ""
echo "   3. Install additional features as needed:"
echo "      pip install openai anthropic  # For AI providers"
echo "      pip install pytest black ruff  # For development"
echo ""
