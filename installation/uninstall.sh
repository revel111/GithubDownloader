#!/bin/bash

DESKTOP_FILE="$HOME/.config/autostart/auto_updater.desktop"

if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    echo "The app has been removed from the startup."
else
    echo "The app was not found in the startup."
fi