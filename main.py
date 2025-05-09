import asyncio
import logging
import sys
import aiohttp  # Add missing import
from aiohttp import web
from aiogram.types import Update
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, TokenBasedRequestHandler, setup_application

# Configure logging - increase level to debug for more information
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from bot.hendlers import setup_routers
from bot.callback import call_router
from bot.middlewares import DbSessionMiddleware

from db import Base, Webhook
from config import *

# Database setup
_engine = create_async_engine(DATABASE_URL)
_sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

# Define bot variable at module level
bot = None

# Add a middleware to log all updates
class LoggingMiddleware:
    async def __call__(self, handler, event, data):
        logger.info(f"Received update: {event}")
        return await handler(event, data)

async def fetch_webhook_urls():
    """Fetch all webhook URLs from the database."""
    async with _sessionmaker() as session:
        query = select(Webhook.webhook_url)
        result = await session.execute(query)
        webhook_urls = [row[0] for row in result.fetchall()]
        logger.info(f"Loaded {len(webhook_urls)} webhook URLs from database")
        return webhook_urls

async def register_webhook_urls(app):
    """Register webhooks for mirror bots."""
    webhook_urls = await fetch_webhook_urls()
    logger.info(f"Setting up {len(webhook_urls)} webhook mirrors")
    
    # Here you would add code to notify each webhook that the server is online
    # or perform any initialization needed for the mirror bots
    async with aiohttp.ClientSession() as session:
        for url in webhook_urls:
            try:
                # Send a ping to each webhook to notify it's online
                logger.info(f"Notifying webhook mirror: {url}")
                await session.post(
                    url,
                    json={"status": "online", "action": "init"},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Error notifying webhook {url}: {e}")

async def on_startup(app) -> None:
    logger.info("Bot starting up...")
    
    # Set webhook for the main bot only
    webhook_url = f"{BASE_URL}{MAIN_BOT_PATH}"
    logger.info(f"Setting webhook to: {webhook_url}")
    
    # First, delete any existing webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Previous webhook deleted")
    
    # Then set the new webhook
    await bot.set_webhook(
        webhook_url,
        allowed_updates=Update.model_fields.keys()    
    )
    logger.info(f"Webhook set to {webhook_url}")
    
    # Get bot info to confirm everything is working
    bot_info = await bot.get_me()
    logger.info(f"Bot authorized as @{bot_info.username} (ID: {bot_info.id})")
    
    # Initialize database
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # Register webhooks for mirror bots from the database
    # The actual webhook handling is done through the multibot_dispatcher
    await register_webhook_urls(app)

async def on_shutdown() -> None:
    # Delete webhook before shutdown to avoid getting updates when bot is offline
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted")
    
    logger.info("Shutting down, closing database connections...")
    # Close database connection pool properly
    await _engine.dispose()
    logger.info("Database connections closed")

# Debug handler to check if updates are being received
async def debug_update(message: Message):
    logger.debug(f"Received update: {message}")
    await message.answer("Debug: Update received!")

async def test_webhook(request):
    """Simple endpoint to test webhook connectivity"""
    logger.info("Test webhook endpoint called")
    return web.json_response({"ok": True, "message": "Webhook endpoint is reachable"})

def main():
    try:
        # Basic setup
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

        # Create session for API calls
        session = AiohttpSession()
        bot_settings = {"session": session}

        # Main bot setup - define globally to use in on_startup/on_shutdown
        global bot
        bot = Bot(token=TOKEN, **bot_settings)

        # Storage for FSM
        storage = MemoryStorage()

        # Main dispatcher for primary bot
        main_dispatcher = Dispatcher(storage=storage)

        # Apply middleware to all types of updates
        main_dispatcher.message.middleware(DbSessionMiddleware(_sessionmaker))
        main_dispatcher.business_message.middleware(DbSessionMiddleware(_sessionmaker))
        main_dispatcher.deleted_business_messages.middleware(DbSessionMiddleware(_sessionmaker))
        main_dispatcher.edited_business_message.middleware(DbSessionMiddleware(_sessionmaker))
        main_dispatcher.callback_query.middleware(DbSessionMiddleware(_sessionmaker))
        # main_dispatcher.update.middleware(LoggingMiddleware())

        # Add debug handler to check if updates are being received
        main_dispatcher.message.register(debug_update, F.text == "/debug")

        # Include our routers
        main_dispatcher.include_router(setup_routers())
        main_dispatcher.include_router(call_router())

        # Register startup/shutdown handlers
        main_dispatcher.startup.register(on_startup)
        main_dispatcher.shutdown.register(on_shutdown)

        # Multibot dispatcher to handle webhook requests for mirror bots
        multibot_dispatcher = Dispatcher(storage=storage)

        # Apply middleware to multibot dispatcher
        multibot_dispatcher.message.middleware(DbSessionMiddleware(_sessionmaker))
        multibot_dispatcher.business_message.middleware(DbSessionMiddleware(_sessionmaker))
        multibot_dispatcher.deleted_business_messages.middleware(DbSessionMiddleware(_sessionmaker))
        multibot_dispatcher.edited_business_message.middleware(DbSessionMiddleware(_sessionmaker))
        multibot_dispatcher.callback_query.middleware(DbSessionMiddleware(_sessionmaker))
        # multibot_dispatcher.update.middleware(LoggingMiddleware())    
    
        # Add debug handler to check if multibot updates are being received
        multibot_dispatcher.message.register(debug_update, F.text == "/debug")
        
        multibot_dispatcher.include_router(setup_routers())
        multibot_dispatcher.include_router(call_router())
        
        # Create web application
        app = web.Application()

        # Add a simple route to test if server is working
        async def health_check(request):
            return web.Response(text="Bot server is running!")
        app.router.add_get('/', health_check)
        app.router.add_get('/test_webhook', test_webhook)

        logger.info(f"Registering webhook handlers for paths:")
        logger.info(f"  - Main bot: {MAIN_BOT_PATH}")
        logger.info(f"  - Other bots: {OTHER_BOTS_PATH}")

        # Register request handlers
        # Main bot - uses a specific path and token
        SimpleRequestHandler(dispatcher=main_dispatcher, bot=bot).register(app, path=MAIN_BOT_PATH)
        
        # Mirror bots - use a token-based path to handle different bots
        TokenBasedRequestHandler(
            dispatcher=multibot_dispatcher,
            bot_settings=bot_settings,
        ).register(app, path=OTHER_BOTS_PATH)

        # Setup handlers
        setup_application(app, main_dispatcher, bot=bot, on_startup=[lambda app: on_startup(app)])
        setup_application(app, multibot_dispatcher)

        logger.info(f"Starting web server on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
        logger.info(f"Bot webhook will be available at {BASE_URL}{MAIN_BOT_PATH}")
        logger.info(f"Multi-bot webhook path: {OTHER_BOTS_PATH}")
        
        # Start web server
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    except Exception as e:
        logger.exception(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
