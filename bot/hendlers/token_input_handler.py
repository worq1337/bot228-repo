import logging
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import BotCreation
from bot.utils.creat import command_add_bot

logger = logging.getLogger(__name__)

def get_token_router() -> Router:
# Create a router
    token_router = Router()

    @token_router.message(BotCreation.waiting_for_token)
    async def process_token_input(message: Message, bot: Bot, state: FSMContext, session: AsyncSession):
        """Process token input when in waiting_for_token state"""
        token = message.text.strip()
        
        # Check if user wants to cancel the operation
        if token.lower() == '/cancel':
            await state.clear()
            return await message.answer("Операция отменена.")
        
        # Clear state first to avoid stuck states if something fails
        await state.clear()
        
        # Use existing command_add_bot function to handle the token
        await command_add_bot(message, bot, token, session)

    @token_router.message(Command("cancel"), BotCreation.waiting_for_token)
    async def cancel_token_input(message: Message, state: FSMContext):
        """Cancel token input process"""
        await state.clear()
        await message.answer("Операция добавления бота отменена.")


    return token_router
