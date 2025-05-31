#!/bin/bash
# UV-native installation for lbrxWhisper
# No venv bullshit - UV handles everything

echo "🚀 lbrxWhisper UV Installation"
echo "=============================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found! Install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# That's it. UV sync does EVERYTHING.
echo ""
echo "📦 Running UV sync..."
uv sync

echo ""
echo "✅ Done! UV installed everything."
echo ""
echo "To run:"
echo "  uv run python run_ultimate_tui.py"
echo ""
echo "With logs:"
echo "  uv run ./run_with_logs.sh"