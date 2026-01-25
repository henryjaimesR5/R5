#!/bin/bash
set -e

echo "🌐 Serving R5 Documentation"
echo "============================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install documentation dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing documentation dependencies..."
    uv sync --group docs
fi

# Serve documentation
echo "🚀 Starting documentation server..."
echo "📖 Open http://127.0.0.1:8000 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uv run mkdocs serve
