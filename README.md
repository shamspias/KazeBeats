# 🎮KazeBeats Discord Music Bot - Ultra Performance Edition

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-blue?logo=discord)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A high-performance, feature-rich Discord music bot with zero-lag streaming, multi-platform support, and a gaming-inspired design. Built with professional architecture and Docker deployment.

## ✨ Features

### 🎵 Core Music Features
- **Zero-lag streaming** with intelligent caching and preloading
- **Multi-platform support**: YouTube, Spotify, SoundCloud, Rutube
- **Multiple instances per server** - Run parallel music sessions
- **High-quality audio**: 320kbps bitrate, 48kHz sample rate
- **Smart queue management** with loop modes (track/queue)

### 🎨 Audio Effects
- **Bass Boost** (0-20 adjustable levels)
- **Karaoke Mode** (vocal removal)
- **Nightcore Effect**
- **3D Audio**
- **Echo Effect**

### 🎮 Gaming Design
- Neon color scheme with vibrant UI
- Interactive embeds with reactions
- Animated progress bars
- Real-time visual feedback

### 🌐 Web Dashboard
- Remote control interface
- Real-time statistics
- Queue management
- Server selection
- WebSocket live updates

### 📊 Advanced Features
- Playlist management
- Lyrics display
- Auto-DJ with recommendations
- Analytics and statistics
- Database persistence

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/shamspias/KazeBeats.git
cd KazeBeats
```

2. **Run setup script**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. **Configure environment**
```bash
cp .env.example .env
nano .env  # Edit with your Discord token
```

4. **Start with Docker Compose**
```bash
make dev  # Development
# or
make prod  # Production
```

5. **Access services**
- Bot: Running in Discord
- Web Dashboard: http://localhost:8080
- Database Admin: http://localhost:8081

### Manual Installation

1. **Install dependencies**
```bash
# System dependencies
sudo apt update
sudo apt install python3.9+ ffmpeg postgresql redis

# Python dependencies
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the bot**
```bash
python src/bot/main.py
```

## 📁 Project Structure

```
discord-music-bot/
├── docker/                 # Docker configuration
│   ├── Dockerfile         # Container configuration
│   └── docker-compose.yml # Multi-container setup
├── src/                   # Source code
│   ├── bot/              # Bot core
│   ├── cogs/             # Command modules
│   ├── core/             # Core functionality
│   ├── database/         # Database models
│   ├── web/              # Web dashboard
│   └── utils/            # Utilities
├── tests/                 # Test suite
├── scripts/              # Automation scripts
├── .env.example          # Environment template
├── docker-compose.yml    # Development compose
├── docker-compose.prod.yml # Production compose
├── Makefile              # Build automation
└── requirements.txt      # Python dependencies
```

## 🛠️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Discord
DISCORD_TOKEN=your_bot_token
DISCORD_PREFIX=!

# Audio
AUDIO_BITRATE=320
DEFAULT_VOLUME=0.5

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Features
ENABLE_WEB_DASHBOARD=true
ENABLE_ANALYTICS=true
ENABLE_AUTO_DJ=false
```

See `.env.example` for all available options.

## 📝 Commands

### Music Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!play <query>` | Search and play music | `!play never gonna give you up` |
| `!join` | Join voice channel | `!join` |
| `!leave` | Leave voice channel | `!leave` |
| `!queue` | Show queue | `!queue` |
| `!skip` | Skip current track | `!skip` |
| `!pause` | Pause playback | `!pause` |
| `!resume` | Resume playback | `!resume` |
| `!loop <mode>` | Set loop mode | `!loop track` |

### Effects Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!bassboost <0-20>` | Apply bass boost | `!bassboost 10` |
| `!karaoke` | Toggle karaoke mode | `!karaoke` |
| `!nightcore` | Toggle nightcore | `!nightcore` |
| `!3d` | Toggle 3D audio | `!3d` |
| `!clearfx` | Clear all effects | `!clearfx` |

### Advanced Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!playlist <action>` | Manage playlists | `!playlist create MyList` |
| `!lyrics` | Show lyrics | `!lyrics` |
| `!stats` | Show statistics | `!stats` |
| `!autodj <on/off>` | Toggle Auto-DJ | `!autodj on` |
| `!instance <action>` | Manage instances | `!instance create party` |

## 🐳 Docker Deployment

### Development
```bash
# Start all services
make dev

# View logs
make logs

# Stop services
make stop
```

### Production
```bash
# Deploy to production
make prod

# Update production
make prod-update

# Backup database
make db-backup

# Monitor services
make monitor
```

### Available Make Commands
```bash
make help          # Show all commands
make dev           # Start development
make prod          # Deploy production
make test          # Run tests
make lint          # Run linters
make format        # Format code
make db-backup     # Backup database
make db-restore    # Restore database
make logs          # View logs
make health        # Check health
make monitor       # Start monitoring
```

## 📊 Monitoring

### Metrics & Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Health checks**: Automated monitoring

Access monitoring:
```bash
make monitor
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

## 🧪 Testing

Run the test suite:
```bash
# Using Make
make test

# Manually
pytest tests/ -v --cov=src

# With Docker
docker-compose exec bot pytest tests/
```

## 🔐 Security

### Best Practices
- Never commit `.env` files
- Use secrets management in production
- Enable rate limiting
- Regular dependency updates
- Use non-root Docker user
- Enable HTTPS for web dashboard

### Security Scanning
```bash
make security  # Run security checks
bandit -r src/  # Code security
safety check    # Dependency vulnerabilities
```

## 📈 Performance

### Optimizations
- **Caching**: Redis for frequently accessed data
- **Preloading**: Next tracks loaded in advance
- **Connection pooling**: Reused database connections
- **Async operations**: Non-blocking I/O
- **Thread pool**: Parallel processing
- **Optimized FFmpeg**: Custom audio pipeline

### Benchmarks
- Latency: < 50ms audio processing
- Memory: ~100-200MB base usage
- CPU: < 5% idle, 10-20% during playback
- Concurrent users: 100+ per instance

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Audio processing
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Redis](https://redis.io/) - Caching
- [Docker](https://www.docker.com/) - Containerization

## 📞 Support

- **Discord Server**: [Join our server](https://discord.gg/your-server)
- **Issues**: [GitHub Issues](https://github.com/yourusername/discord-music-bot/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/discord-music-bot/wiki)

## 🚧 Roadmap

- [ ] Slash commands support
- [ ] Voice commands
- [ ] Mobile app companion
- [ ] AI-powered recommendations
- [ ] Live streaming support
- [ ] Multi-language support
- [ ] Custom audio visualizers
- [ ] Integration with more platforms

---

<div align="center">
  
**Built with ❤️ for the ultimate Discord music experience**

[![Star](https://img.shields.io/github/stars/shamspias/KazeBeats?style=social)](https://github.com/shamspias/KazeBeats)
[![Fork](https://img.shields.io/github/forks/shamspias/KazeBeats?style=social)](https://github.com/shamspias/KazeBeats/fork)
[![Watch](https://img.shields.io/github/watchers/shamspias/KazeBeats?style=social)](https://github.com/shamspias/KazeBeats)

</div>