#!/bin/sh
# Adds STEP to GLB to the app launcher and to "Open with" for STEP files (current user only,
# no root needed). The app stays in this folder: run this again if you move the folder.
# Remove with: ./install.sh --remove
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS="$DATA/applications"
ICONS="$DATA/icons/hicolor/256x256/apps"

if [ "$1" = "--remove" ]; then
    rm -f "$APPS/step2glb.desktop" "$ICONS/step2glb.png"
    update-desktop-database "$APPS" 2>/dev/null || true
    echo "STEP to GLB removed from the launcher (this folder was not deleted)."
    exit 0
fi

mkdir -p "$APPS" "$ICONS"
cp "$DIR/step2glb.png" "$ICONS/step2glb.png"
cat > "$APPS/step2glb.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=STEP to GLB
Comment=Convert STEP CAD files to GLB
Exec="$DIR/STEP2GLB" %F
Icon=step2glb
Terminal=false
Categories=Graphics;3DGraphics;Engineering;
MimeType=model/step;application/step;model/x-step;application/x-step;
StartupWMClass=STEP2GLB
DESKTOP
update-desktop-database "$APPS" 2>/dev/null || true
echo "STEP to GLB added to the launcher: $APPS/step2glb.desktop"
