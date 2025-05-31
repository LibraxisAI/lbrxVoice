#!/bin/bash
# lbrxVoice installer - can be piped from curl
# Usage: curl -fsSL https://raw.githubusercontent.com/LibraxisAI/lbrxVoice/lbrxConversational/install.sh | sh

echo "🚀 Installing lbrxVoice..."
echo "=========================="

# Install to home directory
INSTALL_DIR="$HOME/lbrxVoice"

# Clone repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 Directory exists, updating..."
    cd "$INSTALL_DIR" && git pull
else
    echo "📥 Cloning repository..."
    git clone -b lbrxConversational https://github.com/LibraxisAI/lbrxVoice.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR" || exit 1

# Check for UV
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo "🔧 Installing dependencies..."
uv sync

# Create global command
echo "🚀 Creating lbrxvoice command..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/lbrxvoice" << 'EOF'
#!/bin/bash
cd "$HOME/lbrxVoice" && uv run python run_ultimate_tui.py "$@"
EOF
chmod +x "$HOME/.local/bin/lbrxvoice"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run with: lbrxvoice"
echo "(You may need to restart terminal or add ~/.local/bin to PATH)"
echo ""
echo "No i zajebiście! 🚀"