#!/usr/bin/env bash
set -euo pipefail

printf '\n=== ORBIT v1 installer ===\n'

sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-opencv portaudio19-dev espeak-ng ffmpeg v4l-utils curl git

cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p projects logs

cat > orbit.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=ORBIT
Exec="$(pwd)/.venv/bin/python" "$(pwd)/orbit.py"
Terminal=true
X-GNOME-Autostart-enabled=true
DESKTOP

mkdir -p "$HOME/.config/autostart"
cp orbit.desktop "$HOME/.config/autostart/orbit.desktop"

printf '\nORBIT installation finished.\n'
printf 'Run with: source .venv/bin/activate && python orbit.py\n'
printf 'Optional local AI: install Ollama separately, then pull a small model such as qwen2.5:0.5b.\n'
