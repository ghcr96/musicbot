#!/usr/bin/env bash
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Discord MusicBot installer for Debian LXC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# You can override these if you like:
REPO_URL="${1:-https://github.com/youruser/musicbot.git}"
INSTALL_DIR="/opt/musicbot"
BOT_USER="musicbot"
ENV_FILE="${INSTALL_DIR}/.env"

# 1) Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
  echo "⚠️  Please run as root: sudo ./install.sh"
  exit 1
fi

# 2) Install OS packages
apt update
apt install -y --no-install-recommends \
    git \
    ffmpeg \
    libopus0 libopus-dev \
    python3 python3-venv python3-pip

# 3) Create a dedicated user if missing
if ! id -u "$BOT_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$BOT_USER"
  echo "Created user: $BOT_USER"
fi

# 4) Clone or update the repo
if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "Updating existing repo in $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "Cloning repo into $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 5) Fix permissions
chown -R "$BOT_USER:$BOT_USER" "$INSTALL_DIR"

# 6) Create (or refresh) the Python venv and install deps
sudo -u "$BOT_USER" bash <<EOF
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# 7) Create .env if it doesn’t exist
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<EOL
# Rename this file to .env and set your actual Discord token:
DISCORD_TOKEN=your_bot_token_here
EOL
  chown "$BOT_USER:$BOT_USER" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "🔑 Created .env file at $ENV_FILE (edit with your DISCORD_TOKEN)"
fi

# 8) Install a systemd service
SERVICE_PATH="/etc/systemd/system/musicbot.service"
cat > "$SERVICE_PATH" <<EOL
[Unit]
Description=Discord Music Bot
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

# 9) Enable & start
systemctl daemon-reload
systemctl enable musicbot.service

echo
echo "✅ Installation complete."
echo "1. Edit $ENV_FILE to set your DISCORD_TOKEN."
echo "2. Start the bot:  systemctl start musicbot.service"
echo "3. Check status:      systemctl status musicbot.service"
