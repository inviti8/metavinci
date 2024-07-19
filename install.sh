#!/usr/bin/env bash
set -eo pipefail

echo "Installing Metavinci..."

BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
LOCAL_DIR="${LOCAL_DIR-"$BASE_DIR/.local"}"
HVYM_DIR="$LOCAL_DIR/share/heavymeta-cli"

BIN_URL="https://github.com/inviti8/metavinci/raw/main/build/dist/linux/metavinci"
if [[ "$OSTYPE" == "darwin"* ]]; then
    BIN_URL="https://github.com/inviti8/metavinci/raw/main/build/dist/mac/metavinci"
BIN_PATH="$HVYM_DIR/hvym"

# Create the .foundry bin directory and hvym binary if it doesn't exist.
mkdir -p "$HVYM_DIR"
curl -sSf -L "$BIN_URL" -o "$BIN_PATH"
chmod +x "$BIN_PATH"

# Store the correct profile file (i.e. .profile for bash or .zshenv for ZSH).
case $SHELL in
*/zsh)
    PROFILE="${ZDOTDIR-"$HOME"}/.zshenv"
    PREF_SHELL=zsh
    ;;
*/bash)
    PROFILE=$HOME/.bashrc
    PREF_SHELL=bash
    ;;
*/fish)
    PROFILE=$HOME/.config/fish/config.fish
    PREF_SHELL=fish
    ;;
*/ash)
    PROFILE=$HOME/.profile
    PREF_SHELL=ash
    ;;
*)
    echo "could not detect shell, manually add ${HVYM_DIR} to your PATH."
    exit 1
esac

# Only add hvym if it isn't already in PATH.
if [[ ":$PATH:" != *":${HVYM_DIR}:"* ]]; then
    # Add the hvym directory to the path and ensure the old PATH variables remain.
    # If the shell is fish, echo fish_add_path instead of export.
    if [[ "$PREF_SHELL" == "fish" ]]; then
        echo >> "$PROFILE" && echo "fish_add_path -a $HVYM_DIR" >> "$PROFILE"
    else
        echo >> "$PROFILE" && echo "export PATH=\"\$PATH:$HVYM_DIR\"" >> "$PROFILE"
    fi
fi