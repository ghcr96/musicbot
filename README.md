# Meep 🎵

A feature-rich Discord music bot with automatic updates, comprehensive logging, and easy deployment.

**Current Version: 1.4.0**

## Overview

Meep is a Discord bot written in Python that streams audio from YouTube with advanced queue management, update notifications, and robust error handling. Designed for easy deployment on Proxmox containers with Git integration.

## ✨ Features

### 🎵 Music Playback
- Play audio from YouTube search queries
- Advanced queue management per Discord server
- Skip, pause, resume, and stop controls
- Volume control (0-100%)
- Loop functionality for individual tracks
- Automatic disconnect when queue is empty
- Now playing notifications with dynamic status updates

### 🔄 Auto-Update System
- Automatic version checking from GitHub changelog
- Periodic update notifications (only when out of date)
- Manual update checking with `.checkupdate` command
- Per-channel update notification preferences
- Comprehensive update logging

### 🛠 Management & Monitoring
- Comprehensive logging system with file output
- Real-time status updates in Discord
- Error handling with graceful fallbacks
- Git integration for version control
- Systemd service support for production deployment

### 🎯 Commands

**Playback:**
- `.play <query>` - Search YouTube and play the top result
- `.skip` - Skip the current track
- `.stop` - Stop and leave voice channel
- `.pause` - Pause playback
- `.resume` - Resume playback

**Queue Management:**
- `.queue` - Show current queue
- `.clear` - Clear the queue
- `.nowplaying` - Show current track

**Settings:**
- `.volume <0-100>` - Set volume
- `.loop` - Enable loop (repeat current song)
- `.unloop` - Disable loop

**Updates & Info:**
- `.checkupdate` - Manually check for updates
- `.updatenotify` - Enable update notifications in channel
- `.noupdatenotify` - Disable update notifications in channel
- `.changelog` - Show bot changelog (from GitHub)
- `.version` - Show current version
- `.ping` - Check bot responsiveness

**Utility:**
- `.help` - Show all commands

## 🚀 Quick Installation (Proxmox/Debian/Ubuntu)

**Option 1: Automated Installation Script**
```bash
# Download and run the installation script
wget https://raw.githubusercontent.com/ghcr96/musicbot/main/install.sh
chmod +x install.sh
./install.sh
```

The script will:
- Install all system dependencies (Python, FFmpeg, Opus, Git)
- Set up Python virtual environment
- Configure Git repository
- Create systemd service
- Generate management scripts
- Set up your Discord bot token

**Option 2: Manual Installation**

1. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv git ffmpeg opus-tools libopus0 libopus-dev
   ```

2. **Clone repository:**
   ```bash
   git clone https://github.com/ghcr96/musicbot.git meep-bot
   cd meep-bot
   ```

3. **Set up Python environment:**
   ```bash
   python3 -m venv musicbot-venv
   source musicbot-venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure bot token:**
   ```bash
   cp .env.example .env
   nano .env  # Add your DISCORD_TOKEN=your_token_here
   ```

5. **Run the bot:**
   ```bash
   python musicbot.py
   ```

## 🔧 Management

After installation, use these commands to manage Meep:

```bash
./start.sh     # Start the bot
./stop.sh      # Stop the bot
./status.sh    # Check bot status
./logs.sh      # View real-time logs
./update.sh    # Update from Git and restart
```

Or use systemd directly:
```bash
sudo systemctl start meep-bot
sudo systemctl stop meep-bot
sudo systemctl status meep-bot
sudo journalctl -u meep-bot -f  # View logs
```

## 📋 Prerequisites

- **Python 3.8+**
- **FFmpeg** (for audio processing)
- **Opus libraries** (for Discord voice)
- **Git** (for version control)
- **Discord Bot Token** (from Discord Developer Portal)
- **Linux environment** (Proxmox container, VPS, etc.)

## ⚙️ Configuration

### Environment Variables
Create a `.env` file with:
```bash
DISCORD_TOKEN=your_discord_bot_token_here
```

### GitHub Integration
Update the GitHub URL in `musicbot.py`:
```python
GITHUB_CHANGELOG_URL = \"https://raw.githubusercontent.com/ghcr96/musicbot/main/CHANGELOG.md\"
```

## 📁 Project Structure

```
meep-bot/
├── musicbot.py           # Main bot code
├── requirements.txt      # Python dependencies
├── install.sh           # Automated installation script
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore patterns
├── CHANGELOG.md        # Version history
├── README.md           # This file
├── start.sh            # Start bot script
├── stop.sh             # Stop bot script
├── status.sh           # Status check script
├── logs.sh             # View logs script
├── update.sh           # Update script
└── musicbot-venv/      # Python virtual environment
```

## 🔄 Auto-Update System

Meep includes a sophisticated auto-update system:

1. **Automatic Checks**: Every 6 hours, checks GitHub for new versions
2. **Smart Notifications**: Only notifies when actually out of date
3. **Per-Channel Control**: Enable/disable notifications per channel
4. **Manual Updates**: Use `.checkupdate` for immediate version checking
5. **Comprehensive Logging**: All update checks are logged

### Setting Up Auto-Updates

1. Enable notifications in your Discord channel:
   ```
   .updatenotify
   ```

2. The bot will automatically check for updates every 6 hours

3. When a new version is available, you'll receive a notification

4. Update manually with the provided update script:
   ```bash
   ./update.sh
   ```

## 🐛 Troubleshooting

**Bot not connecting:**
- Check your Discord token in `.env`
- Verify bot has proper permissions in your Discord server

**Audio not working:**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check Opus libraries: `python -c \"import discord; print(discord.opus.is_loaded())\"`

**Update notifications not working:**
- Update GitHub URLs in the code
- Check network connectivity to GitHub
- Review logs: `./logs.sh`

**Service not starting:**
- Check systemd service: `sudo systemctl status meep-bot`
- Review service logs: `sudo journalctl -u meep-bot`

## 📊 Logging

Meep provides comprehensive logging:
- **Console output**: Real-time status updates
- **File logging**: Persistent logs in `musicbot.log`
- **Systemd integration**: Service logs via journalctl
- **Update tracking**: All GitHub API calls logged

View logs:
```bash
./logs.sh                           # Real-time service logs
tail -f musicbot.log                # File logs
sudo journalctl -u meep-bot -f      # Systemd logs
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Logs**: Use logging features for troubleshooting

---
