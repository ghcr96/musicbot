#!/usr/bin/bash

mkdir /home/musicbot/meep
cd /home/musicbot/meep
pwd

apt install git
apt install gh
apt install ffmpeg
apt install libopus0 libopus-dev

gh repo clone ghcr96/musicbot

pip install --upgrade --force-reinstall --break-system-packages \
  "git+https://github.com/Rapptz/discord.py.git@master#egg=discord.py[voice]"

python3 -m pip install discord.py --break-system-packages

python3 -m pip install PyNaCl --break-system-packages

python3 -m pip install yt_dlp --break-system-packages

python3 -m pip install dotenv --break-system-packages

