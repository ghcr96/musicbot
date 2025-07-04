# MusicBot

## Overview

MusicBot is a Discord bot written in Python that streams audio from YouTube based on user commands.

## Features

* Play audio from YouTube search queries
* Manage an in-memory queue per guild
* Skip the current track
* Stop playback and leave the voice channel
* Automatic disconnect when the queue is empty

## Prerequisites

1. Python 3.9 or newer  
2. FFmpeg installed and on your PATH  
3. Opus library installed on your system  
4. A Discord bot token  
5. `pip` and `python` accessible in your environment  

## Installation

Follow these steps to set up the bot locally.

**1. Clone the repository**
```bash
git clone https://github.com/youruser/musicbot.git
cd musicbot
```

**2. Install system dependencies**

On macOS:
```bash
brew install ffmpeg opus
```

On Debian-based systems:
```bash
sudo apt update
sudo apt install ffmpeg libopus0 libopus-dev python3 python3-venv python3-pip git
```

## Proxmox (Optional)

You can deploy the bot in a Proxmox LXC container instead of Docker:

1. **Create a container**: Use a Debian or Ubuntu LXC template in Proxmox.  
2. **Install dependencies**:
   ```bash
   apt update
   apt install -y ffmpeg libopus0 libopus-dev python3 python3-venv python3-pip git
   ```
3. **Clone and set up**:
   ```bash
   git clone https://github.com/youruser/musicbot.git
   cd musicbot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Configure**:  
   Create a `.env` file with your Discord token:
   ```bash
   DISCORD_TOKEN=your_bot_token_here
   ```
5. **Run**:
   ```bash
   nohup python3 musicbot.py &
   ```
6. **(Optional) Systemd service**:  
   Create `/etc/systemd/system/musicbot.service` with:
   ```ini
   [Unit]
   Description=Discord Music Bot
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/root/musicbot
   EnvironmentFile=/root/musicbot/.env
   ExecStart=/root/musicbot/venv/bin/python3 /root/musicbot/musicbot.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
   Then:
   ```bash
   systemctl daemon-reload
   systemctl enable musicbot
   systemctl start musicbot
   ```

## Contributing

Contributions are welcome. Feel free to file issues or submit pull requests.

## License

This project is licensed under the MIT License.
