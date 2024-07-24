#!/usr/bin/env bash
#INSTALL THE DESKTOP
metavinci="$2/bin/metavinci"
icon="$2/app_icon.png"
cat >>/usr/share/applications/metavinci.desktop <<EOL
[Desktop Entry]
Type=Application
Name=Metavinci
Exec=$metavinci
Icon=$icon
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOL
echo "metavinci added to autostart."
