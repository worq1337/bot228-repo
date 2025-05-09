from typing import Any
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.filters import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import Webhook
from config import OTHER_BOTS_URL, BASE_URL

logger = logging.getLogger(__name__)

async def command_add_bot(message: Message, bot: Bot, token: str, session: AsyncSession = None) -> Any:
    try:
        logger.info(f"Adding bot with token: {token[:5]}...{token[-5:]}")
        
        if session:
            existing_token = await session.scalars(select(Webhook).where(Webhook.token == token))
            if existing_token.first():
                return await message.answer("Такой токен уже есть в базе!")
        
        new_bot = Bot(token=token, session=bot.session)
        try:
            bot_user = await new_bot.get_me()
            logger.info(f"Successfully authenticated bot: @{bot_user.username} (ID: {bot_user.id})")
        except TelegramUnauthorizedError:
            logger.warning(f"Invalid token provided: {token[:5]}...{token[-5:]}")
            return await message.answer("Invalid token. Please check and try again.")
        
        # Delete any existing webhook
        await new_bot.delete_webhook(drop_pending_updates=True)

        logger.info(f"Deleted existing webhook for @{bot_user.username}")
        
        # Format the webhook URL
        webhook_url = OTHER_BOTS_URL.format(bot_token=token)
        logger.info(f"Setting webhook for @{bot_user.username} to {webhook_url}")
        
        # Define allowed updates to explicitly include business messages
        allowed_updates = [
            "message", 
            "edited_message", 
            "callback_query", 
            "business_message",
            "edited_business_message",
            "deleted_business_messages"
        ]
        
        # Set the webhook with explicit allowed_updates
        await new_bot.set_webhook(
            webhook_url,
            allowed_updates=allowed_updates
        )
        
        # Verify webhook was set
        webhook_info = await new_bot.get_webhook_info()
        if (webhook_info.url):
            logger.info(f"Webhook successfully set for @{bot_user.username}: {webhook_info.url}")
            
            # Save the webhook to the database
            if session:
                try:
                    # Create a new webhook record
                    new_webhook = Webhook(
                        bot_id=bot_user.id,
                        bot_username=bot_user.username,
                        webhook_url=webhook_url,
                        token=token
                    )
                    session.add(new_webhook)
                    await session.commit()
                    logger.info(f"Webhook for @{bot_user.username} saved to database")
                except Exception as db_error:
                    logger.error(f"Database error saving webhook: {db_error}")
                    await session.rollback()
                    # Continue even if DB save failed - the webhook itself works
            
            return await message.answer(
                f"✅ Bot @{bot_user.username} successfully added!\n"
                f"Bot information saved to database.\n\n"
                f"You can now use this bot as a mirror of the main bot."
            )
        else:
            logger.error(f"Failed to set webhook for @{bot_user.username}")
            return await message.answer(
                f"⚠️ Bot @{bot_user.username} was authenticated but webhook setup failed.\n"
                f"Please try again or contact support."
            )
            
    except Exception as e:
        logger.exception(f"Error adding bot: {e}")
        return await message.answer(f"❌ An error occurred: {str(e)}")


