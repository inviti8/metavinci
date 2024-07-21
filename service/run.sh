#!/usr/bin/env bash
#METAVINCI RUNNER
BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
METAVINCI_DIR="${METAVINCI_DIR-"$BASE_DIR/.metavinci"}"
METAVINCI_BIN_DIR="$METAVINCI_DIR/bin"

metavinci="$METAVINCI_BIN_DIR/metavinci"
$metavinci
# STATUS="$(systemctl is-active metavinci.service)"
# if [ "${STATUS}" = "active" ]; then
# 	metavinci
#     echo "metavinci started"
# else 
#     echo "metavinci could not be started"  
#     exit 1  
# fi
