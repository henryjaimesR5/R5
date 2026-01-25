#!/bin/bash
set -e

echo "🚀 Building R5 Documentation"
echo "=============================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
fi

# Install documentation dependencies
echo "📦 Installing documentation dependencies..."
uv sync --group docs

# Build documentation
echo "📚 Building documentation..."
uv run mkdocs build

echo ""
echo "✅ Documentation built successfully!"
echo "📂 Output: site/"
echo ""
echo "To serve locally:"
echo "  make docs-serve"
echo "  or"
echo "  uv run mkdocs serve"
