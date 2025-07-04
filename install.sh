#!/usr/bin/env bash
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MusicBot installer for Proxmox LXC (Debian/Ubuntu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL_DIR="/opt/musicbot"
BOT_USER="meep"
ENV_FILE="${INSTALL_DIR}/.env"

# 1) Must run as root
if (( EUID != 0 )); then
  echo "⚠️  Please run this as root: sudo $0"
  exit 1
fi

# 2) Install system packages
apt update
apt install -y --no-install-recommends \
    ffmpeg \
    libopus0 libopus-dev \
    python3 python3-venv python3-pip

# 3) Create the bot user if missing
if ! id -u "$BOT_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$BOT_USER"
  echo "Created system user: $BOT_USER"
fi

# 4) Ensure install directory exists & set ownership
mkdir -p "$INSTALL_DIR"
chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"

# 5) Create & activate venv, install Python libs
sudo -u "$BOT_USER" bash <<EOF
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Pull latest discord.py (with voice extra) from GitHub
pip install --force-reinstall \
    "git+https://github.com/Rapptz/discord.py.git@master#egg=discord.py[voice]"
# Other dependencies
pip install PyNaCl yt-dlp python-dotenv
EOF

# 6) Prompt for Discord token & write .env
read -rp "Enter your Discord bot token: " DISCORD_TOKEN
cat > "$ENV_FILE" <<EOL
DISCORD_TOKEN=$DISCORD_TOKEN
EOL
chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# 7) Create systemd service unit
SERVICE_PATH="/etc/systemd/system/musicbot.service"
cat > "$SERVICE_PATH" <<EOL
[Unit]
Description=Discord MusicBot
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/musicbot.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOL

# 8) Enable & start the service
systemctl daemon-reload
systemctl enable musicbot.service
systemctl start musicbot.service

echo
echo "✅ Installation complete!"
echo "   • Place your bot code into $INSTALL_DIR before running."
echo "   • View logs: journalctl -u musicbot -f"
