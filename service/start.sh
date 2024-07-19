#!/usr/bin/env bash
#SETUP METAVINCI AS SERVICE
USER=$(whoami)
BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
METAVINCI_DIR="${METAVINCI_DIR-"$BASE_DIR/.metavinci"}"
METAVINCI_BIN_DIR="$METAVINCI_DIR/bin"
METAVINCI="$METAVINCI_DIR/bin/metavinci"
cat >>/etc/systemd/system/metavinci.service <<EOL
Description=Metavinci Daemon
[Service]
Type=simple
ExecStart=$METAVINCI
User=$USER
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$METAVINCI_BIN_DIR"
[Install]
WantedBy=multi-user.target
EOL
echo "metavinci sevice created."

sudo systemctl daemon-reload
echo "systemctl daemon reloaded."

sudo systemctl enable metavinci
echo "systemctl enabled metavinci"

sudo systemctl start metavinci
echo "systemctl started metavinci"
