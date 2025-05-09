import re
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.creat import command_add_bot


def commands_router() -> Router:
    commands = Router()

    # Helper function to validate the bot token format
    async def is_bot_token(token: str) -> bool:
        # Basic validation - check if token matches expected format
        return bool(re.match(r'^\d+:[\w-]+$', token))

    @commands.message(Command("add_bot"))
    async def add_bot_command(
        message: Message, 
        command: CommandObject, 
        bot: Bot, 
        session: AsyncSession
    ) -> None:
        """Handle the /add_bot command with a token argument"""
        if not command.args:
            await message.answer("Please provide a bot token: /add_bot YOUR_BOT_TOKEN")
            return
        
        token = command.args
        
        # Validate the token format
        if not await is_bot_token(token):
            await message.answer("Invalid token format. Please provide a valid bot token.")
            return
        
        # Call the add_bot function with the extracted token and session
        await command_add_bot(message=message, bot=bot, token=token, session=session)

    return commands
