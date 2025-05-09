from aiogram import Router, F

from .admin import admin_call
from .admin.board import board_router 
from .admin.html_formatter import html_router as html_formatter_router
from .create_bot_callback import create_bot_callback

def call_router() -> Router:
    """Create and configure the callback router."""
    router = Router()
    
    # Register admin callback handlers
    router.callback_query.register(admin_call.full_status, F.data == "full_status")
    router.callback_query.register(admin_call.get_all_users, F.data == "get_all_users")
    router.callback_query.register(admin_call.back_admin_panel, F.data == "back_admin_pnl")
    
    # Register create bot callback handler
    router.callback_query.register(create_bot_callback, F.data == "create_bot")
    
    # Include the broadcast router
    router.include_router(board_router())
    
    # Include the HTML formatter router
    router.include_router(html_formatter_router())
    
    return router
