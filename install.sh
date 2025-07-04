#!/usr/bin/env bash
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MusicBot installer for Proxmox LXC (Debian/Ubuntu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL_DIR="/opt/musicbot"
BOT_USER="meep"
ENV_FILE="$INSTALL_DIR/.env"

# 1) Must run as root
if (( EUID != 0 )); then
  echo "⚠️  Please run this as root: sudo $0"
  exit 1
fi

# 2) Install system packages
apt update
apt install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    git \
    gh  # GitHub CLI

# 3) Authenticate gh CLI with a PAT
read -rp "Enter your GitHub personal access token (repo scope): " GH_TOKEN
echo "$GH_TOKEN" | gh auth login --with-token

# 4) Clone your private repo
read -rp "Enter your GitHub repo (owner/repo): " GH_REPO
mkdir -p "$INSTALL_DIR"
gh repo clone "$GH_REPO" "$INSTALL_DIR"

# 5) Create the bot user if missing
if ! id -u "$BOT_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$BOT_USER"
fi

# 6) Fix ownership
chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"

# 7) Set up Python venv & install libs
sudo -u "$BOT_USER" bash <<EOF
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install discord.py yt-dlp python-dotenv
EOF

# 8) Prompt for Discord token & write .env
read -rp "Enter your Discord bot token: " DISCORD_TOKEN
cat > "$ENV_FILE" <<EOL
DISCORD_TOKEN=$DISCORD_TOKEN
EOL
chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# 9) Create systemd service
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

# 10) Enable & start
systemctl daemon-reload
systemctl enable musicbot.service
systemctl start musicbot.service

echo
echo "✅ MusicBot installed and service started!"
echo "   • Logs:    journalctl -u musicbot -f"
echo "   • To update: rerun this script or 'git -C $INSTALL_DIR pull'"
