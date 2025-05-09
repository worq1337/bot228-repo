from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

# Import routers
from .client import start
from .admin import admin
from .buisness import spy, check
from .commands import commands_router
from .other import other_commands
# Import the token router
from .token_input_handler import get_token_router

def setup_routers() -> Router:
    """Configure all routers."""
    router = Router()
    
    # Include our routers
    router.include_router(other_commands())
    router.include_router(start.start_router())
    router.include_router(admin.admin_router())
    router.include_router(spy.spy_router())
    router.include_router(check.check_router())
    router.include_router(commands_router())
    # Include the token input router
    router.include_router(get_token_router())
    
    return router

async def check_business_capability(message: Message, bot: Bot):
    """Check if the bot can handle business messages"""
    try:
        bot_info = await bot.get_me()
        webhook_info = await bot.get_webhook_info()
        
        response = (
            f"📊 <b>Bot Business Message Capability Check</b>\n\n"
            f"Bot: @{bot_info.username}\n"
            f"Bot ID: {bot_info.id}\n"
            f"Is Business: {'✅ Yes' if bot_info.can_join_groups else '❌ No'}\n"
            f"Webhook URL: {webhook_info.url}\n"
            f"Allowed Updates: {webhook_info.allowed_updates or 'All'}\n\n"
            f"If you want to test business message handling, send <code>.help</code> or <code>.info</code>"
        )
        
        await message.answer(response, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Error checking business capability: {str(e)}")


