import os
import asyncio
import logging
from aiogram import Bot
from aiogram.types import Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from db import MessageCache

logger = logging.getLogger(__name__)


async def business_text_ch(
    msg: Message, 
    bot: Bot, 
    types: str, 
    uid: int, 
    session: AsyncSession, 
    caption: str = 'None'
) -> None:
    """Store message in database using SQLAlchemy."""
    try:
        # Create unique message ID by combining chat and message IDs
        msg_id = int(f"{msg.chat.id}{msg.message_id}")
        
        # Create message cache entry
        message_cache = MessageCache(
            message_id=msg_id,
            chat_id=msg.chat.id,
            user_full_name=msg.from_user.full_name,
            user_id=uid
        )
        
        # Handle different message types
        if types == 'text':
            message_cache.text = msg.text or ''
            message_cache.message_type = types
            message_cache.additional_info = caption
            
        elif types == 'photo':
            message_cache.text = msg.photo[-1].file_id
            message_cache.message_type = types
            message_cache.additional_info = caption or msg.caption or 'None'
            
        elif types == 'video':
            message_cache.text = msg.video.file_id
            message_cache.message_type = types
            message_cache.additional_info = caption or msg.caption or 'None'
            
        elif types == 'video_note':
            message_cache.text = msg.video_note.file_id
            message_cache.message_type = types
            message_cache.additional_info = caption
            
        elif types == 'voice':
            message_cache.text = msg.voice.file_id
            message_cache.message_type = types
            message_cache.additional_info = caption
        
        # Save to database
        session.add(message_cache)
        logger.debug(f"Cached {types} message {msg_id}")
        
    except Exception as e:
        logger.exception(f"Error caching message: {e}")
        await session.rollback()


async def handle_media(msg, file_type: str, media_path: str, media_caption: str, media_method, connection, bot):
    """Process and save media files from messages."""
    try:
        media = getattr(msg.reply_to_message, file_type)
        bot_name = await bot.get_me()
        
        if isinstance(media, list):
            media_file = media[-1]  # Get highest quality
        else:
            media_file = media
            
        md = ['GA', 'Fg', 'Fw', 'GQ']

        file_id = media_file.file_id
        file = await bot.get_file(file_id)
        check = file.file_id[0:2]
        
        if check in md:
            # Create directory if it doesn't exist
            if not os.path.exists(media_path):
                os.makedirs(media_path)
                
            local_file_path = f"{media_path}/{file.file_path.split('/')[-1]}"
            await bot.download_file(file.file_path, local_file_path)

            # Create FSInputFile for uploading
            media_file = FSInputFile(local_file_path)
            caption = f'<b>☝️Сохранено с помощью @{bot_name.username}</b>'

            # Send appropriate media type
            if file_type == 'photo':
                await media_method(connection.user.id, photo=media_file, caption=caption, parse_mode='HTML')
            elif file_type == 'video':
                await media_method(connection.user.id, video=media_file, caption=caption, parse_mode='HTML')
            elif file_type == 'voice':
                await media_method(connection.user.id, voice=media_file, caption=caption, parse_mode='HTML')
            elif file_type == 'video_note':
                await media_method(connection.user.id, video=media_file, caption=caption, parse_mode='HTML')

            # Clean up
            os.remove(local_file_path)
            await asyncio.sleep(0.05)
        
    except Exception as e:
        logger.exception(f"Error handling {file_type}: {e}")
        await bot.send_message(connection.user.id, f"Ошибка: Не удалось обработать {file_type}.")
