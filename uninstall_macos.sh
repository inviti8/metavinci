#!/bin/bash
# macOS Uninstall Script for Metavinci
# This script cleans up the hvym CLI and related files when Metavinci is uninstalled

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Metavinci Uninstaller for macOS${NC}"
echo "=================================="

# Get the user's home directory
USER_HOME="$HOME"
METAVINCI_CONFIG_DIR="$USER_HOME/Library/Application Support/Metavinci"
METAVINCI_BIN_DIR="$METAVINCI_CONFIG_DIR/bin"
# Possible hvym binary names (architecture-aware and legacy)
HVYM_CANDIDATES=(
  "$METAVINCI_BIN_DIR/hvym-macos-arm64"
  "$METAVINCI_BIN_DIR/hvym-macos-amd64"
  "$METAVINCI_BIN_DIR/hvym-macos"
)

echo "Looking for Metavinci installation..."

# Check if Metavinci config directory exists
if [ ! -d "$METAVINCI_CONFIG_DIR" ]; then
    echo -e "${YELLOW}No Metavinci installation found at: $METAVINCI_CONFIG_DIR${NC}"
    exit 0
fi

echo "Found Metavinci installation at: $METAVINCI_CONFIG_DIR"

# Remove hvym CLI binary if it exists (any known name)
removed_any=false
for candidate in "${HVYM_CANDIDATES[@]}"; do
  if [ -f "$candidate" ]; then
    echo "Removing hvym CLI binary: $candidate"
    rm -f "$candidate"
    removed_any=true
  fi
done

if [ "$removed_any" = true ]; then
  echo -e "${GREEN}✓ Removed hvym CLI binary${NC}"
else
  echo -e "${YELLOW}hvym CLI binary not found${NC}"
fi

# Remove bin directory if it's empty
if [ -d "$METAVINCI_BIN_DIR" ]; then
    if [ -z "$(ls -A "$METAVINCI_BIN_DIR")" ]; then
        echo "Removing empty bin directory..."
        rmdir "$METAVINCI_BIN_DIR"
        echo -e "${GREEN}✓ Removed empty bin directory${NC}"
    else
        echo -e "${YELLOW}Bin directory not empty, leaving it in place${NC}"
    fi
fi

# Remove config directory if it's empty
if [ -d "$METAVINCI_CONFIG_DIR" ]; then
    if [ -z "$(ls -A "$METAVINCI_CONFIG_DIR")" ]; then
        echo "Removing empty config directory..."
        rmdir "$METAVINCI_CONFIG_DIR"
        echo -e "${GREEN}✓ Removed empty config directory${NC}"
    else
        echo -e "${YELLOW}Config directory not empty, leaving it in place${NC}"
    fi
fi

echo -e "${GREEN}✓ Metavinci uninstallation completed successfully${NC}"
echo ""
echo "Note: This script only removes the hvym CLI and related files."
echo "To completely uninstall Metavinci, also remove the .app bundle from Applications."
