#!/bin/bash
# lbrxVoice installer - can be piped from curl
# Usage: curl -fsSL https://raw.githubusercontent.com/LibraxisAI/lbrxVoice/main/install.sh | sh

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
    git clone https://github.com/LibraxisAI/lbrxVoice.git "$INSTALL_DIR"
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

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "📝 Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run lbrxVoice:"
echo "  lbrxvoice"
echo ""
echo "Or if command not found:"
echo "  source ~/.zshrc"
echo "  lbrxvoice"
echo ""
echo "Alternative:"
echo "  ~/.local/bin/lbrxvoice"
echo ""
echo "No i zajebiście! 🚀"