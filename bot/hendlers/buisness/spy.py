import os
import asyncio
import logging
from typing import Callable, Any

from aiogram import Router, Bot, F
from aiogram.types import Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils import business_text_ch, handle_media

# Configure logger
def spy_router() -> Router:
    logger = logging.getLogger(__name__)
    router = Router()

    # ==================== MESSAGE HANDLERS ====================

    @router.business_message(F.text)
    async def business_text_handler(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle text messages in business chats."""
        try:
            feedback = msg.business_connection_id
            connection = await bot.get_business_connection(feedback)

            # Different handling for replies vs direct messages
            if not msg.reply_to_message:
                # Direct message
                await business_text_ch(
                    msg=msg,
                    bot=bot,
                    types='text',
                    caption='None',
                    uid=connection.user.id,
                    session=session
                )
            else:
                # Reply to a message
                user_connection = await bot.get_business_connection(feedback)

                # Check if the user is replying to their own message
                if msg.from_user.id == user_connection.user.id:
                    # Handle different types of replied media
                    if msg.reply_to_message.photo:
                        await handle_media(msg, "photo", "photos", "Фото", bot.send_photo, user_connection, bot)
                    elif msg.reply_to_message.video:
                        await handle_media(msg, "video", "videos", "Видео", bot.send_video, user_connection, bot)
                    elif msg.reply_to_message.video_note:
                        await handle_media(msg, "video_note", "videos", "Видео заметка", bot.send_video, user_connection, bot)
                    elif msg.reply_to_message.voice:
                        await handle_media(msg, "voice", "videos", "Голосовое", bot.send_voice, user_connection, bot)
                    else:
                        await business_text_ch(
                            msg=msg,
                            bot=bot,
                            types='text',
                            caption='None',
                            uid=user_connection.user.id,
                            session=session
                        )
                else:
                    # Handle reply from someone else
                    await business_text_ch(
                        msg=msg,
                        bot=bot,
                        types='text',
                        caption='None',
                        uid=user_connection.user.id,
                        session=session
                    )
        except Exception as e:
            logger.exception(f"Error handling business text: {e}")


    @router.business_message(F.photo)
    async def business_photo_handler(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle photo messages in business chats."""
        try:
            feedback = msg.business_connection_id
            connection = await bot.get_business_connection(feedback)

            await business_text_ch(
                msg=msg,
                bot=bot,
                types='photo',
                caption=msg.caption,
                uid=connection.user.id,
                session=session
            )

        except Exception as e:
            logger.exception(f"Error handling business photo: {e}")


    @router.business_message(F.video)
    async def business_video_handler(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle video messages in business chats."""
        try:
            feedback = msg.business_connection_id
            connection = await bot.get_business_connection(feedback)

            await business_text_ch(
                msg=msg,
                bot=bot,
                types='video',
                caption=msg.caption,
                uid=connection.user.id,
                session=session
            )

        except Exception as e:
            logger.exception(f"Error handling business video: {e}")


    @router.business_message(F.video_note)
    async def business_video_note_handler(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle video note messages in business chats."""
        try:
            feedback = msg.business_connection_id
            connection = await bot.get_business_connection(feedback)

            await business_text_ch(
                msg=msg,
                bot=bot,
                types='video_note',
                caption=msg.caption,
                uid=connection.user.id,
                session=session
            )

        except Exception as e:
            logger.exception(f"Error handling business video note: {e}")


    @router.business_message(F.voice)
    async def business_voice_handler(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle voice messages in business chats."""
        try:
            feedback = msg.business_connection_id
            connection = await bot.get_business_connection(feedback)

            await business_text_ch(
                msg=msg,
                bot=bot,
                types='voice',
                caption=msg.caption,
                uid=connection.user.id,
                session=session
            )

        except Exception as e:
            logger.exception(f"Error handling business voice: {e}")

    return router
