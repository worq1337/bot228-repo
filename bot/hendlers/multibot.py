import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandStart, CommandObject

# Import original handlers to reuse their functionality
from bot.hendlers.client.start import start
from bot.hendlers.other import (
    helper, love, love2, get_info, deanon, 
    ghule, doxer, animeted_text
)
from bot.hendlers.commands import add_bot_command
from bot.utils.check import is_bot_token

logger = logging.getLogger(__name__)

# Create a dedicated router for multibot handlers
def setup_multibot_router() -> Router:
    router = Router(name="multibot_router")
    
    # Register command handlers - using the actual handlers from the main bot
    router.message.register(start, CommandStart())
    
    # Register the add_bot command
    router.message.register(add_bot_command, Command("add_bot"))
    
    # Register other message handlers - using the actual handlers from other.py
    router.business_message.register(helper, F.text==".help") 
    router.business_message.register(love, F.text==".love") 
    router.business_message.register(love2, F.text==".love2") 
    router.business_message.register(get_info, F.text==".info") 
    # Commented out handlers that might be problematic
    # router.business_message.register(spammer, F.text.startswith('.spam'))
    # router.business_message.register(crash, F.text==".crash") 
    # router.business_message.register(crash2, F.text==".crash2")
    router.business_message.register(deanon, F.text==".deanon") 
    router.business_message.register(ghule, F.text==".-7") 
    router.business_message.register(doxer, F.text==".dox")
    router.business_message.register(animeted_text, Command("p")) 
    
    # Import admin handlers if needed
    try:
        # If these imports fail, the bot will still work but without admin functionality
        from bot.hendlers.admin.admin import setup_admin_handlers
        setup_admin_handlers(router)
    except ImportError as e:
        logger.warning(f"Could not load admin handlers for mirror bot: {e}")
    
    # Import spy handlers if needed
    try:
        from bot.hendlers.buisness.spy import setup_spy_handlers
        setup_spy_handlers(router)
    except ImportError as e:
        logger.warning(f"Could not load spy handlers for mirror bot: {e}")
    
    # Import check handlers if needed
    try:
        from bot.hendlers.buisness.check import setup_check_handlers
        setup_check_handlers(router)
    except ImportError as e:
        logger.warning(f"Could not load check handlers for mirror bot: {e}")
        
    return router

