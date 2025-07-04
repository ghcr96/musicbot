#!/usr/bin/env bash
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MusicBot installer for Proxmox LXC (Debian/Ubuntu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL_DIR="/opt/musicbot"
BOT_USER="meep"
ENV_FILE="${INSTALL_DIR}/.env"

# 1) root check
if (( EUID != 0 )); then
  echo "⚠️  Please run as root: sudo $0"
  exit 1
fi

# 2) update & install system deps
apt update
apt install -y --no-install-recommends \
    git \
    gh \
    ffmpeg \
    libopus0 libopus-dev \
    python3 python3-venv python3-pip

# 3) create meep user if needed
if ! id -u "$BOT_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$BOT_USER"
  echo "Created system user: $BOT_USER"
fi

# 4) prompt to authenticate GitHub CLI (one-time)
echo "👉 Please authenticate the GitHub CLI now:"
gh auth login --web

# 5) clone your private repo
read -rp "GitHub repo (owner/repo): " GH_REPO
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
chown "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"
sudo -u "$BOT_USER" gh repo clone "$GH_REPO" "$INSTALL_DIR"

# 6) set ownership
chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"

# 7) set up Python venv & install libs
sudo -u "$BOT_USER" bash <<'EOF'
cd "$HOME/../opt/musicbot"  # resolves to /opt/musicbot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install git+https://github.com/Rapptz/discord.py.git@master#egg=discord.py[voice]
pip install PyNaCl yt-dlp python-dotenv
EOF

# 8) ask for Discord token
read -rp "Enter your Discord bot token: " DISCORD_TOKEN
cat > "$ENV_FILE" <<EOL
DISCORD_TOKEN=$DISCORD_TOKEN
EOL
chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# 9) create systemd service
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

# 10) enable and start
systemctl daemon-reload
systemctl enable musicbot.service
systemctl start musicbot.service

echo
echo "✅ MusicBot installed and running under user '$BOT_USER'."
echo "   • Check logs with: journalctl -u musicbot -f"
