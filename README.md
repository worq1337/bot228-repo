# SaveMod - Telegram Business Bot Mirror

Advanced Telegram bot system for creating and managing mirror instances of the SaveMod business bot.

## Features

- **SaveMod Bot Management**: Central control panel for all mirror bots
- **Mirror Bot Creation**: Create replicas of SaveMod with unique tokens
- **Business Message Support**: Full support for Telegram's Business features
- **Webhook Architecture**: Efficient handling of multiple bot instances
- **State Management**: Interactive token input flow with proper state transitions

## Technical Stack

- Python 3.12+
- aiogram 3.18
- PostgreSQL with asyncpg
- Asynchronous architecture with asyncio
- aiohttp for webhook server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/B880OO/savemod_bot.git
cd savemod_bot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Essential environment variables:
- `TOKEN`: Your main Telegram bot token
- `DATABASE_URL`: PostgreSQL connection string
- `BASE_URL`: Public URL for your webhook server
- `WEB_SERVER_HOST` and `WEB_SERVER_PORT`: Server binding settings
- `MAIN_BOT_PATH`: Webhook path for main bot
- `OTHER_BOTS_PATH`: Path pattern for mirror bots

## Usage

1. Start the bot:
```bash
python main.py
```

2. Access the admin panel through your main SaveMod bot
3. Use the "Create Mirror Bot" option to create a SaveMod mirror
4. Follow on-screen instructions to set up a new SaveMod mirror

## Architecture

The system uses a combination of:
- Central dispatcher for the main bot
- Token-based request handler for mirror bots
- FSM (Finite State Machine) for multi-step operations
- Custom middleware for database session management

## Project Structure

```
savemod_bot/
├── main.py                   # Application entry point and web server setup
├── config.py                 # Environment variables and configuration
├── db/
│   ├── __init__.py           # Database models and session setup
│   └── models.py             # SQLAlchemy ORM models
├── bot/
│   ├── __init__.py           # Bot initialization
│   ├── middlewares.py        # Middleware components for request processing
│   ├── states/               # FSM state definitions
│   │   ├── __init__.py
│   │   └── bot_states.py     # States for bot creation flow
│   ├── hendlers/             # Message handlers
│   │   ├── __init__.py       # Router setup
│   │   ├── admin/            # Admin command handlers
│   │   ├── client/           # User command handlers
│   │   ├── buisness/         # Business message handlers
│   │   ├── commands/         # General commands
│   │   ├── other/            # Miscellaneous handlers
│   │   └── token_input_handler.py # Token input processing
│   ├── callback/             # Callback query handlers
│   │   ├── __init__.py       # Callback router
│   │   ├── admin/            # Admin panel callbacks
│   │   └── create_bot_callback.py # Bot creation flow
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── creat.py          # Mirror bot creation logic
├── requirements.txt          # Project dependencies
├── .env.example              # Example environment configuration
└── README.md                 # Project documentation
```

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

## License

MIT License

## Advanced Configuration

### Webhooks

For production use, ensure your server meets these requirements:
- Valid HTTPS certificate (self-signed not recommended)
- Open ports for webhook communication
- Properly configured reverse proxy (nginx/Apache)

Example nginx configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /webhook/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Business Message Support

This bot fully supports Telegram's Business API features:
- Business messages (requires Business Bot mode enabled)
- Message controls
- Customer chat management
- Automated responses

## Deployment

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
docker build -t telegram-business-bot .
docker run -d --name business-bot --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  telegram-business-bot
```

### Systemd Service (Linux)

For running as a system service:

```ini
[Unit]
Description=Telegram Business Bot Mirror
After=network.target postgresql.service

[Service]
User=botuser
Group=botuser
WorkingDirectory=/path/to/bot
ExecStart=/path/to/bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Webhook not working**
   - Ensure your SSL certificate is valid
   - Check that ports are open and properly forwarded
   - Verify the BASE_URL is correctly set in .env

2. **Database connection errors**
   - Confirm PostgreSQL is running
   - Check DATABASE_URL format and credentials
   - Ensure proper permissions are set

3. **Bot not responding**
   - Verify the token is valid
   - Check for errors in the logs
   - Ensure webhook is properly set

### Logs

Logs are crucial for troubleshooting:
```bash
tail -f logs/bot.log
```

## Security Considerations

- Store tokens securely using environment variables
- Implement rate limiting to prevent abuse
- Validate all incoming data
- Run the bot with minimal permissions

## Credits and Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - The foundation of our bot framework
- Telegram API team for the Business Bot features
- SaveMod Bot developers and contributors

## Contact

For support or questions about SaveMod, please open an issue on GitHub or contact the maintainer at:
comdodo69@gmail.com
Telegram: https://t.me/woxhook

