"""
Web dashboard for KazeBeats
Real-time control and statistics with gaming design
"""

from aiohttp import web
import aiohttp_cors
import json
from datetime import datetime
import os


def create_app(bot):
    """Create web application with routes"""
    app = web.Application()
    app['bot'] = bot

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Routes
    routes = web.RouteTableDef()

    @routes.get('/')
    async def index(request):
        """Serve main dashboard page"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KazeBeats Dashboard - Gaming Music Experience</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #fff;
            overflow-x: hidden;
        }

        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(0, 212, 255, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(157, 0, 255, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, rgba(255, 0, 220, 0.3) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
            pointer-events: none;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(-20px, -20px) rotate(1deg); }
            66% { transform: translate(20px, -10px) rotate(-1deg); }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 1;
        }

        header {
            text-align: center;
            margin-bottom: 3rem;
            animation: slideDown 0.8s ease-out;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        h1 {
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(45deg, #00d4ff, #ff00dc, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            margin-bottom: 0.5rem;
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.5)); }
            to { filter: drop-shadow(0 0 30px rgba(255, 0, 220, 0.8)); }
        }

        .tagline {
            font-size: 1.2rem;
            opacity: 0.9;
            color: #00ff88;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            animation: fadeIn 0.8s ease-out forwards;
            opacity: 0;
        }

        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }

        @keyframes fadeIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
            from {
                opacity: 0;
                transform: translateY(20px);
            }
        }

        .stat-card:hover {
            transform: translateY(-5px) scale(1.02);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }

        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 0 10px currentColor);
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(45deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .control-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 2rem;
        }

        .now-playing {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(255, 0, 220, 0.1));
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 2px solid rgba(0, 255, 136, 0.3);
            position: relative;
            overflow: hidden;
        }

        .now-playing::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #00d4ff, #ff00dc, #00ff88, #00d4ff);
            border-radius: 20px;
            opacity: 0.5;
            animation: borderRotate 3s linear infinite;
            z-index: -1;
        }

        @keyframes borderRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .track-info {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .track-art {
            width: 100px;
            height: 100px;
            border-radius: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .track-details h3 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #00ff88;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-top: 1rem;
            overflow: hidden;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            border-radius: 10px;
            width: 45%;
            animation: progressPulse 1s ease-in-out infinite;
        }

        @keyframes progressPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        .control-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
            flex-wrap: wrap;
        }

        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: none;
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.5s ease;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-primary {
            background: linear-gradient(45deg, #00d4ff, #00ff88);
        }

        .btn-danger {
            background: linear-gradient(45deg, #ff0040, #ff6b00);
        }

        .servers-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }

        .server-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .server-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: scale(1.05);
        }

        .server-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, #00d4ff, #ff00dc);
            margin: 0 auto 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }

        footer {
            text-align: center;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            opacity: 0.7;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00ff88;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            h1 { font-size: 2.5rem; }
            .container { padding: 1rem; }
            .stat-card { padding: 1rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎮 KazeBeats</h1>
            <p class="tagline">Gaming-Inspired Discord Music Experience</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🎵</div>
                <div class="stat-value" id="songs-played">0</div>
                <div class="stat-label">Songs Played</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📡</div>
                <div class="stat-value" id="servers">0</div>
                <div class="stat-label">Servers</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-value" id="users">0</div>
                <div class="stat-label">Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-value" id="commands">0</div>
                <div class="stat-label">Commands</div>
            </div>
        </div>

        <div class="now-playing">
            <h2>🎧 Now Playing</h2>
            <div class="track-info">
                <div class="track-art">🎵</div>
                <div class="track-details">
                    <h3 id="track-title">No track playing</h3>
                    <p id="track-artist">Start playing music in Discord!</p>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>

        <div class="control-panel">
            <h2>🎮 Control Panel</h2>
            <div class="control-buttons">
                <button class="btn btn-primary" onclick="refreshStats()">
                    🔄 Refresh Stats
                </button>
                <button class="btn" onclick="viewQueue()">
                    📋 View Queue
                </button>
                <button class="btn" onclick="viewServers()">
                    🌐 View Servers
                </button>
                <button class="btn btn-danger" onclick="clearCache()">
                    🗑️ Clear Cache
                </button>
            </div>
        </div>

        <div id="servers-container"></div>

        <footer>
            <p>KazeBeats v1.0.0 | High-Performance Discord Music Bot</p>
            <p>Made with 💜 for the gaming community</p>
        </footer>
    </div>

    <script>
        // Auto-refresh stats
        async function refreshStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                document.getElementById('songs-played').textContent = formatNumber(data.songs_played);
                document.getElementById('servers').textContent = formatNumber(data.servers);
                document.getElementById('users').textContent = formatNumber(data.users);
                document.getElementById('commands').textContent = formatNumber(data.commands);

                // Update now playing
                if (data.now_playing) {
                    document.getElementById('track-title').textContent = data.now_playing.title;
                    document.getElementById('track-artist').textContent = data.now_playing.artist;
                }
            } catch (error) {
                console.error('Failed to refresh stats:', error);
            }
        }

        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toString();
        }

        async function viewQueue() {
            alert('Queue viewer coming soon!');
        }

        async function viewServers() {
            const response = await fetch('/api/servers');
            const servers = await response.json();

            let html = '<h2>🌐 Connected Servers</h2><div class="servers-list">';
            servers.forEach(server => {
                html += `
                    <div class="server-card">
                        <div class="server-icon">🎮</div>
                        <h4>${server.name}</h4>
                        <p>${server.members} members</p>
                    </div>
                `;
            });
            html += '</div>';

            document.getElementById('servers-container').innerHTML = html;
        }

        async function clearCache() {
            if (confirm('Are you sure you want to clear the cache?')) {
                await fetch('/api/cache/clear', { method: 'POST' });
                alert('Cache cleared successfully!');
            }
        }

        // Initial load and auto-refresh
        refreshStats();
        setInterval(refreshStats, 5000);
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type='text/html')

    @routes.get('/api/stats')
    async def stats(request):
        """Get bot statistics"""
        bot = request.app['bot']

        # Get current playing track
        now_playing = None
        for guild in bot.guilds:
            if guild.voice_client and guild.voice_client.playing:
                player = guild.voice_client
                if player.current:
                    now_playing = {
                        'title': player.current.title,
                        'artist': player.current.author or 'Unknown',
                        'guild': guild.name
                    }
                    break

        stats = {
            'songs_played': bot.songs_played,
            'servers': len(bot.guilds),
            'users': len(bot.users),
            'commands': bot.commands_executed,
            'uptime': str(datetime.utcnow() - bot.start_time),
            'now_playing': now_playing
        }

        return web.json_response(stats)

    @routes.get('/api/servers')
    async def servers(request):
        """Get list of servers"""
        bot = request.app['bot']

        servers_list = []
        for guild in bot.guilds:
            servers_list.append({
                'id': str(guild.id),
                'name': guild.name,
                'members': guild.member_count,
                'playing': bool(guild.voice_client and guild.voice_client.playing)
            })

        return web.json_response(servers_list)

    @routes.get('/api/queue/{guild_id}')
    async def queue(request):
        """Get queue for specific guild"""
        bot = request.app['bot']
        guild_id = int(request.match_info['guild_id'])

        guild = bot.get_guild(guild_id)
        if not guild or not guild.voice_client:
            return web.json_response({'error': 'Guild not found or not playing'}, status=404)

        player = guild.voice_client
        queue_list = []

        for track in player.queue:
            queue_list.append({
                'title': track.title,
                'author': track.author,
                'duration': track.length // 1000,
                'requester': str(track.requester) if hasattr(track, 'requester') else 'Unknown'
            })

        return web.json_response({
            'guild': guild.name,
            'queue': queue_list,
            'loop_mode': player.loop_mode
        })

    @routes.post('/api/cache/clear')
    async def clear_cache(request):
        """Clear bot cache"""
        bot = request.app['bot']
        bot.cache.clear()

        return web.json_response({'status': 'success', 'message': 'Cache cleared'})

    @routes.get('/health')
    async def health(request):
        """Health check endpoint"""
        return web.json_response({'status': 'healthy'})

    # Add routes to app
    app.add_routes(routes)

    # Setup CORS for all routes
    for route in list(app.router.routes()):
        cors.add(route)

    return app
