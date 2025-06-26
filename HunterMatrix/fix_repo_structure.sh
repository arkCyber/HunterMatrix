#!/bin/bash

# Fix HunterMatrix repository structure
# Move all files from HunterMatrix subdirectory to root

echo "🔧 Fixing HunterMatrix repository structure..."

# Create a temporary directory
TEMP_DIR="/tmp/huntermatrix_temp_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📁 Created temporary directory: $TEMP_DIR"

# Copy all files except .git to temp directory
echo "📋 Copying files to temporary directory..."
rsync -av --exclude='.git' --exclude='fix_repo_structure.sh' . "$TEMP_DIR/"

# Remove all files except .git and this script
echo "🧹 Cleaning current directory..."
find . -maxdepth 1 -not -name '.git' -not -name 'fix_repo_structure.sh' -exec rm -rf {} +

# Move files from temp back to current directory
echo "📦 Moving files back to root directory..."
mv "$TEMP_DIR"/* .
mv "$TEMP_DIR"/.[^.]* . 2>/dev/null || true

# Clean up temp directory
echo "🗑️ Cleaning up temporary directory..."
rm -rf "$TEMP_DIR"

echo "✅ Repository structure fixed!"
echo "📝 Next steps:"
echo "   1. git add ."
echo "   2. git commit -m 'Fix repository structure'"
echo "   3. git push"
