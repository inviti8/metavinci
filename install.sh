#!/usr/bin/env bash
set -eo pipefail

echo "Installing metavinci..."

BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
METAVINCI_DIR="${METAVINCI_DIR-"$BASE_DIR/.metavinci"}"
METAVINCI_BIN_DIR="$METAVINCI_DIR/bin"

BIN_URL="https://github.com/inviti8/metavinci/raw/main/build/dist/linux/metavinci"
BIN_PATH="$METAVINCI_BIN_DIR/metavinci"

# Create the .metavinci bin directory and metavinci binary if it doesn't exist.
mkdir -p "$METAVINCI_BIN_DIR"
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
    echo "metavinci: could not detect shell, manually add ${METAVINCI_BIN_DIR} to your PATH."
    exit 1
esac

# Only add metavinci if it isn't already in PATH.
if [[ ":$PATH:" != *":${METAVINCI_BIN_DIR}:"* ]]; then
    # Add the metavinci directory to the path and ensure the old PATH variables remain.
    # If the shell is fish, echo fish_add_path instead of export.
    if [[ "$PREF_SHELL" == "fish" ]]; then
        echo >> "$PROFILE" && echo "fish_add_path -a $METAVINCI_BIN_DIR" >> "$PROFILE"
    else
        echo >> "$PROFILE" && echo "export PATH=\"\$PATH:$METAVINCI_BIN_DIR\"" >> "$PROFILE"
    fi
fi

. ~/.bashrc
echo
echo "Detected your preferred shell is $PREF_SHELL and added metavinci to PATH."
echo "Run 'source $PROFILE' or start a new terminal session to use metavinci."
echo "Then, simply run 'metavinci' to install Metavinci."