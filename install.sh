#!/usr/bin/env bash
# Sets up the virtualenv and adds the app to the desktop menu as "Frame TV".
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q --upgrade pip
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
cat > "$APPS/frame-tv.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Frame TV
Comment=Choose an image and show it in Art Mode on a Samsung The Frame
Comment[tr]=Resim seç, Samsung The Frame'de Sanat Modu'nda göster
Exec="$DIR/.venv/bin/python" "$DIR/frame_app.py"
Path=$DIR
Icon=video-display
Terminal=false
Categories=Graphics;Utility;
DESKTOP

echo "Done. The app shows up in the menu as 'Frame TV'."
echo "First time? Run .venv/bin/python connect.py and press Allow on the TV screen."
