#!/bin/bash

sh ~/Downloads/pycharm-2025.1.1.1/bin/pycharm.sh &
steam -applaunch 238960

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script is in: $SCRIPT_DIR"
cat "$SCRIPT_DIR/../data/input.txt"

#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Find the latest matching AppImage file
APPIMAGE=$(ls -1 "$SCRIPT_DIR"/Awakened-PoE-Trade-*.AppImage 2>/dev/null | sort -V | tail -n 1)

if [[ -x "$APPIMAGE" ]]; then
    "$APPIMAGE"
else
    echo "No Awakened-PoE-Trade AppImage found in $SCRIPT_DIR"
    exit 1
fi