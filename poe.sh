#!/bin/bash

code ~/PycharmProjects/pypoe &
steam -applaunch 238960

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
APPIMAGE=$(ls -1 "$SCRIPT_DIR"/Awakened-PoE-Trade-*.AppImage 2>/dev/null | sort -V | tail -n 1)
if [[ -x "$APPIMAGE" ]]; then
    "$APPIMAGE" &
else
    echo "No Awakened-PoE-Trade AppImage found in $SCRIPT_DIR"
    exit 1
fi
