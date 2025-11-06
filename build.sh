#!/usr/bin/env bash
set -e

echo "🔨 Buildingnedok..."

# Clean previous builds
rm -rf build dist *.spec

# Build
poetry run pyinstaller \
    --onefile \
    --name nedok \
    --clean \
    --strip \
    src/nedok/cli.py

echo "✅ Build complete!"
echo "📦 Binary: dis/tnedok"
echo ""
echo "Test it:"
echo "  ./dist/nedok"
