# Meep Discord Music Bot Changelog

## [1.4.5] - 2024-07-30

### Fixed
- **Voice Connection Success**: Discord voice connection now works properly
- **FFmpeg Integration**: Fixed FFmpeg dependency for audio source creation
- **Connection Stability**: Resolved error 4006 with discord.py 2.3.2

### Success
- **Voice Handshake**: Successfully connecting to Discord voice channels
- **Audio Processing**: Ready for FFmpeg-based audio streaming
- **Container Compatibility**: Confirmed working in Proxmox LXC containers

## [1.4.4] - 2024-07-30

### Fixed
- **Discord.py Version Compatibility**: Pinned discord.py to stable version 2.3.2
- **yt-dlp Updates**: Updated to latest yt-dlp version for YouTube compatibility
- **Voice Connection Stability**: Improved voice connection handling for error 4006

### Changed
- **Dependency Versions**: Locked discord.py to tested compatible version
- **YouTube Support**: Updated yt-dlp for better video extraction
- **Library Stability**: Focused on proven stable library versions

## [1.4.3] - 2024-07-30

### Added
- **Network Diagnostics**: Added comprehensive network connectivity debugging
- **Container Support**: Enhanced support for Proxmox/LXC container deployments
- **Voice Server Debugging**: Detailed logging for Discord voice server connections

### Technical Improvements
- **UDP Connectivity**: Better handling of container network limitations
- **Voice Timeout**: Extended voice connection timeout for slow networks
- **Error Documentation**: Added specific error code explanations and fixes

## [1.4.2] - 2024-07-30

### Fixed
- **Discord Voice Connection Issues**: Fixed error code 4006 (Session no longer valid)
- **Voice Connection Timeout**: Added proper timeout handling for voice connections
- **Connection Error Handling**: Enhanced error messages for voice connection failures
- **Bot Intents**: Added required voice_states and guilds intents for proper voice functionality

### Technical Improvements
- **Voice Connection Logging**: Added detailed logging for voice connection attempts
- **Reconnection Logic**: Improved voice connection with timeout and reconnect parameters
- **Error Specificity**: Specific error handling for different voice connection failure types
- **Connection Stability**: Better handling of voice channel moves and reconnections

## [1.4.1] - 2024-07-30

### Fixed
- **Audio Streaming Issues**: Enhanced error handling for audio playback failures
- **Join/Leave Loop**: Fixed bot joining and immediately leaving voice channels
- **Stream URL Validation**: Better handling of invalid or expired YouTube stream URLs
- **FFmpeg Error Handling**: Comprehensive error reporting for audio source creation
- **Playback Debugging**: Added detailed logging for audio playback troubleshooting

### Technical Improvements
- **Enhanced Error Reporting**: All audio failures now provide specific error messages
- **Playback Logging**: Detailed logs for audio source creation and playback events
- **Stream Debugging**: Added debug logging for YouTube stream URLs
- **Callback Error Handling**: Improved error handling in audio playback callbacks
- **Next Song Protection**: Error handling for queue progression failures

## [1.4.0] - 2024-07-30

### Added
- **Auto-Update System**: Automatic version checking from GitHub changelog every 6 hours
- **Update Notifications**: Discord notifications when new versions are available (only when out of date)
- **Update Management Commands**: 
  - `.checkupdate` - Manually check for updates
  - `.updatenotify` - Enable update notifications in channel
  - `.noupdatenotify` - Disable update notifications in channel
- **GitHub Integration**: Live changelog fetching from GitHub repository
- **Comprehensive Update Logging**: All GitHub API calls and version checks are logged
- **Enhanced Documentation**: Complete README.md with installation and usage guide

### Changed
- **Changelog Source**: Now fetched live from GitHub instead of hardcoded
- **Repository Integration**: Fully integrated with https://github.com/ghcr96/musicbot.git

### Technical Improvements
- **Semantic Versioning**: Proper version comparison logic for updates
- **Error Handling**: Robust error handling for GitHub API failures
- **Logging Enhancement**: All version checks logged with detailed information
- **Channel Management**: Per-channel update notification preferences with cleanup
- **Async HTTP**: Added aiohttp dependency for GitHub API calls

## [1.3.0] - 2024-12-30

### Added
- **Security Improvements**: Token moved to .env file with proper validation
- **Logging System**: Comprehensive logging with file output (musicbot.log) and timestamps
- **Error Handling**: Robust error handling for startup, runtime, and connection issues
- **Dependencies Management**: Added requirements.txt for easy installation
- **Code Quality**: Better organization, logging, and best practices

### Fixed
- **Token Security**: Removed hardcoded token, now uses environment variables
- **Error Messages**: More informative error messages for common issues
- **Startup Validation**: Bot validates configuration before starting

### Changed
- **Logging**: Replaced print statements with proper logging system
- **Error Handling**: More graceful handling of Discord API errors
- **Code Structure**: Improved imports and error handling organization

## [1.2.0] - 2024-12-19

### Added
- **Dynamic Status Updates**: Bot status now changes based on current activity
  - Shows "🎵 [Song Title]" when playing
  - Shows "🔁 [Song Title]" when looping
  - Shows "⏸ Paused" when paused
  - Shows "🎵 .help for commands" when idle
- **Automatic Queue Progression**: Bot announces when songs change
  - "⏵ Now playing: **Song Title**" for new songs
  - "🔁 Looping: **Song Title**" for looped songs
- **Improved Help Command**: Single message with organized categories
- **Latency Display**: Ping command now shows bot latency in milliseconds
- **Auto-Disconnect**: Bot automatically leaves voice channel when queue is empty

### Fixed
- **Skip Command Bug**: Fixed issue where bot would replay first song after skipping
- **Loop Functionality**: Proper loop state management per guild
- **Queue Management**: Songs are properly removed from queue when skipped
- **Status Consistency**: Bot status updates correctly across all commands
- **Error Handling**: Better error messages and validation

### Changed
- **Code Structure**: Refactored to use Discord.py Cogs for better organization
- **Security**: Removed hardcoded token, now uses environment variables
- **Status Management**: Centralized status update function
- **Queue Logic**: Improved queue progression and cleanup

## [1.1.0] - 2024-12-19

### Added
- **Loop Command**: Enable/disable song looping
- **Queue Management**: View and clear queue
- **Volume Control**: Adjust bot volume (0-100)
- **Pause/Resume**: Control playback
- **Now Playing**: Show current track information
- **Basic Commands**: Play, skip, stop functionality

### Fixed
- **Typo**: Fixed `@bot.commmand` → `@bot.command`
- **Loop Logic**: Proper loop state storage per guild
- **Queue Consistency**: Fixed initial song addition to queue

## [1.0.0] - 2024-12-19

### Added
- **Initial Release**: Basic Discord music bot
- **YouTube Integration**: Search and play YouTube videos
- **Voice Channel Support**: Join, play, and leave voice channels
- **Basic Commands**: Play, stop, skip functionality
- **Queue System**: Basic song queuing
- **FFmpeg Integration**: Audio streaming support

---

## Commands Reference

### Playback Commands
- `.play <query>` - Search YouTube and play the top result
- `.skip` - Skip the current track
- `.stop` - Stop and leave voice channel
- `.pause` - Pause playback
- `.resume` - Resume playback

### Queue Management
- `.queue` - Show current queue
- `.clear` - Clear the queue
- `.nowplaying` - Show current track

### Settings
- `.volume <0-100>` - Set volume
- `.loop` - Enable loop (repeat current song)
- `.unloop` - Disable loop

### Utility
- `.ping` - Check bot responsiveness and latency
- `.help` - Show all commands

---

## Technical Details

### Dependencies
- discord.py
- yt-dlp
- python-dotenv
- FFmpeg (system dependency)

### Features
- Multi-guild support (separate queues per server)
- Audio format optimization (best audio-only streams)
- Automatic Opus library loading
- Error handling and validation
- Dynamic status updates
- Queue persistence per guild

### Architecture
- Discord.py Cogs for modular command organization
- Asynchronous audio playback with callbacks
- Thread-safe status updates
- Environment-based configuration 