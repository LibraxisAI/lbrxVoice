#!/bin/bash
# Switch to Dragon configuration

echo "🐉 Switching to Dragon (512GB M3 Ultra)..."

# Copy Dragon env
cp .env.dragon .env

echo "✅ Configuration switched!"
echo ""
echo "Dragon endpoint: http://100.82.232.70:1234"
echo ""
echo "Make sure Dragon is accessible via Tailscale:"
echo "  tailscale status | grep dragon"
echo ""
echo "To switch back to local:"
echo "  rm .env"