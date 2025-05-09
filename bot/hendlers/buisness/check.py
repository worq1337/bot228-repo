import logging
import typing
import time
import asyncio

from aiogram import Router, Bot, F
from aiogram.types import Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import MessageCache

# Configure logger
def check_router() -> Router:
    logger = logging.getLogger(__name__)
    router = Router(name=__name__)

    # Define message action constants
    ACTION_EDIT = "edit"
    ACTION_DELETE = "delete"

    class RecentsItem(typing.NamedTuple):
        """Store information about recent message changes."""
        timestamp: int
        chat_id: int
        message_id: int
        action: str
        old_text: typing.Optional[str] = None
        new_text: typing.Optional[str] = None

        @classmethod
        def from_edit(cls, message: Message, old_text: str) -> "RecentsItem":
            return cls(
                timestamp=int(time.time()),
                chat_id=message.chat.id,
                message_id=message.message_id,
                action=ACTION_EDIT,
                old_text=old_text,
                new_text=message.text,
            )


    async def check_message(message_id: int, bot: Bot, session: AsyncSession) -> None:
        """Check if a deleted message exists in cache, notify user, and delete it."""
        try:
            # Get the message from cache
            stmt = select(MessageCache).where(MessageCache.message_id == message_id)
            cached_message = await session.scalar(stmt)
            
            if cached_message:
                # Extract message data
                user_id = cached_message.user_id
                chat_id = cached_message.chat_id
                sender_name = cached_message.user_full_name
                message_content = cached_message.text
                msg_type = cached_message.message_type
                caption = cached_message.additional_info
                
                # Delete the message from cache
                await session.delete(cached_message)
                
                # Send appropriate notifications based on message type
                if msg_type == 'text':
                    await bot.send_message(user_id,
                        text=f"🗑 Это сообщение было удалено:\n\n"
                            f"Отправитель: <a href='tg://user?id={chat_id}'><b>{sender_name}</b></a>\n"
                            f"Текст: <blockquote><b>{message_content}</b></blockquote>",
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.05)
                    
                elif msg_type == 'photo':
                    await bot.send_photo(user_id,
                        photo=message_content,
                        caption=f"🗑 Это фото было удалено:\n\n"
                                f"Отправитель: <a href='tg://user?id={chat_id}'><b>{sender_name}</b></a>\n"
                                f"{f'С содержанием: <code><b>{caption}</b></code>' if caption and caption != 'None' else ''}",
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.05)
                    
                elif msg_type == 'video':
                    await bot.send_video(user_id,
                        video=message_content,
                        caption=f"🗑 Это видео было удалено:\n\n"
                                f"Отправитель: <a href='tg://user?id={chat_id}'><b>{sender_name}</b></a>\n"
                                f"{f'С содержанием: <code><b>{caption}</b></code>' if caption and caption != 'None' else ''}",
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.05)
                    
                elif msg_type == 'video_note':
                    await bot.send_video(user_id,
                        video=message_content,
                        caption=f"🗑 Это видео было удалено:\n\n"
                                f"Отправитель: <a href='tg://user?id={chat_id}'><b>{sender_name}</b></a>\n"
                                f"{f'С содержанием: <code><b>{caption}</b></code>' if caption and caption != 'None' else ''}",
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.05)
                    
                elif msg_type == 'voice':
                    await bot.send_voice(user_id,
                        voice=message_content,
                        caption=f"🗑 Это голосовое было удалено:\n\n"
                                f"Отправитель: <a href='tg://user?id={chat_id}'><b>{sender_name}</b></a>\n"
                                f"{f'С содержанием: <code><b>{caption}</b></code>' if caption and caption != 'None' else ''}",
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(0.05)
                    
                logger.info(f"Notification sent for deleted {msg_type} message {message_id}")
                
        except Exception as e:
            logger.exception(f"Error checking deleted message: {e}")


    @router.edited_business_message(F.text)
    async def business_edit(message: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle edited business messages."""
        try:
            # Create a unique message ID
            msg_id = int(f"{message.chat.id}{message.message_id}")
            
            # Get connection info
            feedback = message.business_connection_id
            connection = await bot.get_business_connection(feedback)
            
            # Find message in cache
            stmt = select(MessageCache).where(MessageCache.message_id == msg_id)
            cached_message = await session.scalar(stmt)
            
            if cached_message:
                # Create recent item with old text
                old_text = cached_message.text
                recent_item = RecentsItem.from_edit(message, old_text)
                
                # Update the message in cache
                cached_message.text = message.text
                
                # Skip if user edited their own message
                if message.from_user.id == cached_message.user_id:
                    return
                    
                # Send notification about edit
                await bot.send_message(
                    cached_message.user_id,
                    f"🔏 Пользователь <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> "
                    f"изменил сообщение:\n\n"
                    f"Старый текст: <blockquote><b>{old_text}</b></blockquote>\n"
                    f"Новый текст: <blockquote><b>{recent_item.new_text}</b></blockquote>",
                    parse_mode="HTML"
                )
                
            else:
                # Create new cache entry if not found
                new_cache = MessageCache(
                    message_id=msg_id,
                    chat_id=message.chat.id,
                    user_full_name=message.from_user.full_name,
                    text=message.text,
                    message_type="text",
                    additional_info="none",
                    user_id=connection.user.id
                )
                session.add(new_cache)
                
                # Skip notification if it's the user's own message
                if message.from_user.id == connection.user.id:
                    return
                    
                # Send notification without old text
                await bot.send_message(
                    connection.user.id,
                    f"🔏 Пользователь <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> "
                    f"изменил сообщение, но старый текст отсутствует в кэше.\n\n"
                    f"Новый текст: <blockquote><b>{message.text}</b></blockquote>",
                    parse_mode="HTML"
                )
                
            # Small delay to avoid race conditions
            await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.exception(f"Error handling edited message: {e}")


    @router.deleted_business_messages()
    async def business_delete(msg: Message, bot: Bot, session: AsyncSession) -> None:
        """Handle deleted business messages."""
        try:
            for message_id in msg.message_ids:
                # Create unique message ID
                full_msg_id = int(f"{msg.chat.id}{message_id}")
                # Check and process the deleted message
                await check_message(message_id=full_msg_id, bot=bot, session=session)
        except Exception as e:
            logger.exception(f"Error handling deleted messages: {e}")

    return router
