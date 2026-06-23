#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Academic Dashboard macOS build..."

# 1. Clean old build files
echo "🧹 Cleaning old build files..."
rm -rf build/dist build/build build/dmg_root dist/ releases/*.dmg

# 2. Run PyInstaller
echo "📦 Compiling application with PyInstaller..."
.venv/bin/pyinstaller --noconfirm "Academic Dashboard.spec"

# 3. Prepare DMG root
echo "📂 Preparing DMG root directory..."
mkdir -p build/dmg_root
cp -R "dist/Academic Dashboard.app" build/dmg_root/

# 4. Check for create-dmg
if command -v create-dmg &> /dev/null; then
    echo "💿 Creating styled DMG installer..."
    create-dmg \
      --volname "Academic Dashboard" \
      --background "assets/dmg_background.png" \
      --window-pos 200 120 \
      --window-size 600 400 \
      --icon-size 100 \
      --icon "Academic Dashboard.app" 175 190 \
      --hide-extension "Academic Dashboard.app" \
      --app-drop-link 425 190 \
      "releases/AcademicDashboard_macos_universal.dmg" \
      "build/dmg_root/"
else
    echo "⚠️ Warning: 'create-dmg' is not installed. Creating fallback standard DMG..."
    ln -s /Applications build/dmg_root/Applications
    hdiutil create -volname "Academic Dashboard" -srcfolder build/dmg_root -ov -format UDZO "releases/AcademicDashboard_macos_universal.dmg"
fi

echo "✅ Build complete! Installer is available at: releases/AcademicDashboard_macos_universal.dmg"
