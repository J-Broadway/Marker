#!/bin/bash
cd "$(dirname "$0")"

# Minimize this terminal window immediately
osascript -e 'tell application "Terminal" to set miniaturized of front window to true' &

# Run the GUI
.venv/bin/python marker.py

# Close this terminal window when GUI exits
osascript -e 'tell application "Terminal" to close (every window whose name contains "marker.command")' 2>/dev/null &
exit 0
