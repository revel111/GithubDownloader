#!/usr/bin/env bash

pip install -r requirements.txt --break-system-packages

SCRIPT_PATH="$(dirname "$(pwd)")/auto_updater.pyw"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/auto_updater.desktop"

mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Type=Application
Exec=/usr/bin/python3 $SCRIPT_PATH
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=GithubLoader
Comment=Startup
EOL

chmod +x "$DESKTOP_FILE"

echo "The installation is successful."