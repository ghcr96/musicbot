#!/usr/bin/env bash
set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MusicBot installer for Proxmox LXC (Debian/Ubuntu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTALL_DIR="/opt/musicbot"
BOT_USER="meep"
ENV_FILE="${INSTALL_DIR}/.env"

# 1) Ensure script is run as root
if (( EUID != 0 )); then
  echo "Error: this script must be run as root (or via sudo)." >&2
  exit 1
fi

# 2) Determine how to run commands as the bot user
if (( EUID == 0 )); then
  # We're root → use su
  AS_USER_CMD="su - ${BOT_USER} -s /bin/bash -c"
else
  # Not root → use sudo
  AS_USER_CMD="sudo -u ${BOT_USER}"
fi

# 3) Install system dependencies
apt update
apt install -y --no-install-recommends \
    git \
    ffmpeg \
    libopus0 libopus-dev \
    python3 python3-venv python3-pip

# 4) Create the bot user if it doesn’t exist
if ! id -u "$BOT_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$BOT_USER"
  echo "Created system user: $BOT_USER"
fi

# 5) Prepare installation directory
mkdir -p "$INSTALL_DIR"
chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_DIR"

# 6) Set up Python virtual environment and install libraries
$AS_USER_CMD "bash << 'EOF'
cd \"$INSTALL_DIR\"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Install latest discord.py from GitHub with voice support
pip install --force-reinstall \
    \"git+https://github.com/Rapptz/discord.py.git@master#egg=discord.py[voice]\"
pip install PyNaCl yt-dlp python-dotenv
EOF
"

# 7) Prompt for Discord token and write .env
read -rp "Enter your Discord bot token: " DISCORD_TOKEN
cat > "$ENV_FILE" <<EOF
DISCORD_TOKEN=$DISCORD_TOKEN
EOF
chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# 8) Create systemd service unit
SERVICE_PATH="/etc/systemd/system/musicbot.service"
cat > "$SERVICE_PATH" <<EOF
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
EOF

# 9) Enable and start the service
systemctl daemon-reload
systemctl enable musicbot.service
systemctl start musicbot.service

echo "Installation complete. MusicBot is now running under user '$BOT_USER'."
echo "View live logs with: journalctl -u musicbot -f"
