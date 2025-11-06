#!/usr/bin/env bash
set -e

echo "🔨 Building nedok..."

# Clean previous builds
rm -rf build dist

# Build using spec file
poetry run pyinstaller --clean --strip nedok.spec

echo "✅ Build complete!"
echo "📦 Binary: dist/nedok"
echo ""
echo "Test it:"
echo "  ./dist/nedok --version"
