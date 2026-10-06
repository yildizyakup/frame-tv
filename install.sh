#!/usr/bin/env bash
# Sanal ortamı kurar ve uygulamayı masaüstü menüsüne "Frame TV" olarak ekler.
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
Comment=Resim seç, Samsung The Frame'de Sanat Modu'nda göster
Exec="$DIR/.venv/bin/python" "$DIR/frame_app.py"
Path=$DIR
Icon=video-display
Terminal=false
Categories=Graphics;Utility;
DESKTOP

echo "Kurulum tamam. Menüde 'Frame TV' olarak görünecek."
echo "İlk kez bağlanıyorsanız: .venv/bin/python connect.py (TV ekranında İzin Ver'e basın)"
