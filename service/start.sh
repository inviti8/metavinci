#!/usr/bin/env bash
#SETUP METAVINCI AS SERVICE
metavinci="$2/bin/metavinci"
icon="$2/app_icon.png"
cat >>/usr/share/applications/metavinci.desktop <<EOL
[Desktop Entry]
Type=Application
Name=Metavinci Daemon
Exec=$metavinci
Icon=$icon
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOL
echo "metavinci added to autostart."

# sudo chown $SUDO_USER /home/$1/.config/autostart/metavinci.desktop

# sudo chown $SUDO_USER /home/$1/.config/autostart/metavinci.desktop

# chmod 644 /home/$1/.config/autostart/metavinci.desktop
