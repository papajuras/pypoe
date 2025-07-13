#!/bin/bash

sh ~/Downloads/pycharm-2025.1.1.1/bin/pycharm.sh &
steam -applaunch 238960

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script is in: $SCRIPT_DIR"
cat "$SCRIPT_DIR/../data/input.txt"

"$SCRIPT_DIR"/Awakened-PoE-Trade-3.25.104.AppImage