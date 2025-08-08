#!/bin/bash
# Linux Uninstall Script for Metavinci
# This script cleans up the hvym CLI and related files when Metavinci is uninstalled

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Metavinci Uninstaller for Linux${NC}"
echo "=================================="

# Get the user's home directory
USER_HOME="$HOME"
HVYM_DIR="$USER_HOME/.local/share/heavymeta-cli"
HVYM_BINARY="$HVYM_DIR/hvym-linux"

echo "Looking for Metavinci installation..."

# Check if hvym directory exists
if [ ! -d "$HVYM_DIR" ]; then
    echo -e "${YELLOW}No hvym CLI installation found at: $HVYM_DIR${NC}"
    exit 0
fi

echo "Found hvym CLI installation at: $HVYM_DIR"

# Remove hvym CLI binary if it exists
if [ -f "$HVYM_BINARY" ]; then
    echo "Removing hvym CLI binary..."
    rm -f "$HVYM_BINARY"
    echo -e "${GREEN}✓ Removed hvym CLI binary${NC}"
else
    echo -e "${YELLOW}hvym CLI binary not found${NC}"
fi

# Remove hvym directory if it's empty
if [ -d "$HVYM_DIR" ]; then
    if [ -z "$(ls -A $HVYM_DIR)" ]; then
        echo "Removing empty hvym directory..."
        rmdir "$HVYM_DIR"
        echo -e "${GREEN}✓ Removed empty hvym directory${NC}"
    else
        echo -e "${YELLOW}hvym directory not empty, leaving it in place${NC}"
    fi
fi

echo -e "${GREEN}✓ Metavinci uninstallation completed successfully${NC}"
echo ""
echo "Note: This script only removes the hvym CLI and related files."
echo "To completely uninstall Metavinci, also run: sudo dpkg -r com.metavinci.desktop"
