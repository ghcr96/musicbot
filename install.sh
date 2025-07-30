#!/bin/bash

# Meep Discord Music Bot Installation Script
# For Proxmox containers running Debian/Ubuntu

set -e  # Exit on any error

echo "🎵 Installing Meep Discord Music Bot..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons."
   print_status "Please run as a regular user with sudo privileges."
   exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect OS. This script supports Debian/Ubuntu systems."
    exit 1
fi

print_status "Detected OS: $OS $VER"

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    opus-tools \
    libopus0 \
    libopus-dev \
    curl \
    wget \
    nano \
    htop \
    systemd

print_success "System dependencies installed"

# Set up directory structure
MEEP_DIR="$HOME/meep-bot"
print_status "Setting up Meep directory at $MEEP_DIR"

if [ -d "$MEEP_DIR" ]; then
    print_warning "Directory $MEEP_DIR already exists"
    read -p "Do you want to remove it and start fresh? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$MEEP_DIR"
        print_status "Removed existing directory"
    else
        print_status "Using existing directory"
    fi
fi

mkdir -p "$MEEP_DIR"
cd "$MEEP_DIR"

# Initialize Git repository or clone from remote
print_status "Setting up Git repository..."
if [ ! -d ".git" ]; then
    read -p "Enter your Git repository URL (or press Enter to initialize new repo): " GIT_REPO
    if [ -n "$GIT_REPO" ]; then
        print_status "Cloning from $GIT_REPO"
        git clone "$GIT_REPO" .
    else
        print_status "Initializing new Git repository"
        git init
        git config --global init.defaultBranch main
    fi
fi

# Set up Git configuration if not already configured
if [ -z "$(git config --global user.name)" ]; then
    read -p "Enter your Git username: " GIT_USERNAME
    git config --global user.name "$GIT_USERNAME"
fi

if [ -z "$(git config --global user.email)" ]; then
    read -p "Enter your Git email: " GIT_EMAIL
    git config --global user.email "$GIT_EMAIL"
fi

print_success "Git repository configured"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv musicbot-venv
source musicbot-venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    print_status "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    print_status "Installing Python dependencies manually..."
    pip install discord.py>=2.3.0 yt-dlp>=2023.7.6 python-dotenv>=1.0.0 PyNaCl>=1.5.0 aiohttp>=3.8.0
    
    # Create requirements.txt
    cat > requirements.txt << EOF
discord.py>=2.3.0
yt-dlp>=2023.7.6
python-dotenv>=1.0.0
PyNaCl>=1.5.0
aiohttp>=3.8.0
EOF
fi

print_success "Python dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    read -p "Enter your Discord bot token: " DISCORD_TOKEN
    cat > .env << EOF
DISCORD_TOKEN=$DISCORD_TOKEN
EOF
    print_success ".env file created"
else
    print_warning ".env file already exists, skipping token setup"
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/meep-bot.service > /dev/null << EOF
[Unit]
Description=Meep Discord Music Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$MEEP_DIR
Environment=PATH=$MEEP_DIR/musicbot-venv/bin
ExecStart=$MEEP_DIR/musicbot-venv/bin/python musicbot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable meep-bot.service

print_success "Systemd service created and enabled"

# Create update script
print_status "Creating update script..."
cat > update.sh << 'EOF'
#!/bin/bash
# Meep Bot Update Script

echo "🔄 Updating Meep Bot..."
cd "$(dirname "$0")"

# Stop the service
sudo systemctl stop meep-bot.service

# Pull latest changes from Git
git pull origin main

# Activate virtual environment
source musicbot-venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Start the service
sudo systemctl start meep-bot.service

echo "✅ Meep Bot updated and restarted"
EOF

chmod +x update.sh
print_success "Update script created"

# Create start/stop scripts
cat > start.sh << EOF
#!/bin/bash
sudo systemctl start meep-bot.service
echo "✅ Meep Bot started"
EOF

cat > stop.sh << EOF
#!/bin/bash
sudo systemctl stop meep-bot.service
echo "⏹ Meep Bot stopped"
EOF

cat > status.sh << EOF
#!/bin/bash
sudo systemctl status meep-bot.service
EOF

cat > logs.sh << EOF
#!/bin/bash
sudo journalctl -u meep-bot.service -f
EOF

chmod +x start.sh stop.sh status.sh logs.sh
print_success "Management scripts created"

# Final setup instructions
echo
echo "🎉 Installation Complete!"
echo "========================"
echo
print_status "Meep Discord Bot has been installed to: $MEEP_DIR"
print_status "Virtual environment: $MEEP_DIR/musicbot-venv"
print_status "Service name: meep-bot.service"
echo
print_status "Management commands:"
echo "  ./start.sh    - Start the bot"
echo "  ./stop.sh     - Stop the bot"
echo "  ./status.sh   - Check bot status"
echo "  ./logs.sh     - View bot logs"
echo "  ./update.sh   - Update from Git"
echo
print_status "Systemd commands:"
echo "  sudo systemctl start meep-bot    - Start the bot"
echo "  sudo systemctl stop meep-bot     - Stop the bot"
echo "  sudo systemctl restart meep-bot  - Restart the bot"
echo "  sudo systemctl status meep-bot   - Check status"
echo
if [ ! -f "musicbot.py" ]; then
    print_warning "musicbot.py not found in current directory"
    print_status "Make sure to add your bot files to this directory"
    print_status "Or clone from your Git repository"
fi

print_status "To start the bot now, run: ./start.sh"
print_status "To view logs, run: ./logs.sh"

echo
print_success "Installation completed successfully! 🎵"