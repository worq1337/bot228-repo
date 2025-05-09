import asyncio
import logging
import aiohttp
import time
import uuid
import json
import io
import os
import shutil
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
import re

from aiogram import Bot, F, Router
from aiogram.types import (
    Message, 
    CallbackQuery, 
    ContentType,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Spyusers, Webhook
from config import ADMIN


def board_router() -> Router:
    logger = logging.getLogger(__name__)
    router = Router()

    # FSM States for broadcast
    class BroadcastForm(StatesGroup):
        select_type = State()            # Select broadcast type (users or webhooks)
        waiting_for_message = State()    # Waiting for the message to broadcast
        add_buttons = State()            # Ask if buttons should be added
        button_text = State()            # Enter button text
        button_url = State()             # Enter button URL
        button_add_more = State()        # Ask if more buttons should be added
        preview = State()                # Preview message before sending
        confirm = State()                # Confirm sending

    # Storage for cancel flags 
    cancel_flags = {}
    
    @router.callback_query(F.data == "board")
    async def start_broadcast(clb: CallbackQuery, state: FSMContext):
        """Start the broadcast creation process."""
        if clb.from_user.id not in ADMIN:
            await clb.answer("Доступ запрещен", show_alert=True)
            return
        
        # Offer a choice between user broadcast or webhook broadcast
        await clb.message.edit_text(
            "📢 <b>Создание рассылки</b>\n\n"
            "Выберите тип рассылки:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Пользователям", callback_data="broadcast_users")],
                [InlineKeyboardButton(text="🔗 Webhook-зеркалам", callback_data="broadcast_webhooks")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin_pnl")]
            ])
        )
        await state.set_state(BroadcastForm.select_type)
        await clb.answer()
    
    @router.callback_query(F.data == "broadcast_users", BroadcastForm.select_type)
    async def select_users_broadcast(clb: CallbackQuery, state: FSMContext):
        """Select user broadcast."""
        await state.update_data(broadcast_type="users")
        
        await clb.message.edit_text(
            "📢 <b>Создание рассылки для пользователей</b>\n\n"
            "Отправьте сообщение, которое хотите разослать всем пользователям.\n"
            "Поддерживаются: текст, фото, видео, документы, аудио и анимации.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить создание", callback_data="cancel_broadcast_creation")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_broadcast_type")]
            ])
        )
        await state.set_state(BroadcastForm.waiting_for_message)
        await clb.answer()
    
    @router.callback_query(F.data == "broadcast_webhooks", BroadcastForm.select_type)
    async def select_webhooks_broadcast(clb: CallbackQuery, state: FSMContext, session: AsyncSession):
        """Select webhook broadcast with improved error handling."""
        # Check if there are any webhooks
        webhooks = await get_all_webhooks(session)
        
        # Debug log the webhooks
        logger.info(f"Found webhooks: {webhooks}")
        
        if not webhooks:
            await clb.message.edit_text(
                "❌ <b>Не найдено ни одного webhook.</b>\n\n"
                "Сначала добавьте webhook URL в базу данных.\n"
                "Проверьте, что webhook был успешно сохранен в базе.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_broadcast_type")]
                ])
            )
            await clb.answer()
            return
        
        await state.update_data(broadcast_type="webhooks", webhooks=webhooks)
        
        await clb.message.edit_text(
            "📢 <b>Создание рассылки для webhook-зеркал</b>\n\n"
            f"Найдено webhook-зеркал: <b>{len(webhooks)}</b>\n\n"
            "Отправьте сообщение, которое хотите разослать на все webhook-зеркала.\n"
            "Поддерживаются: текст, фото, видео, документы, аудио и анимации.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить создание", callback_data="cancel_broadcast_creation")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_broadcast_type")]
            ])
        )
        await state.set_state(BroadcastForm.waiting_for_message)
        await clb.answer()
    
    @router.callback_query(F.data == "back_to_broadcast_type")
    async def back_to_broadcast_type(clb: CallbackQuery, state: FSMContext):
        """Go back to broadcast type selection."""
        await start_broadcast(clb, state)
        await clb.answer()

    async def get_all_webhooks(session: AsyncSession) -> List[str]:
        """Get all webhook URLs from the database with improved error handling."""
        try:
            # More specific query to ensure we get all webhooks
            query = select(Webhook.webhook_url).where(Webhook.webhook_url.isnot(None))
            result = await session.execute(query)
            webhooks = [row[0] for row in result.fetchall()]
            
            # Log the number of webhooks found
            logger.info(f"Retrieved {len(webhooks)} webhooks from database")
            if not webhooks:
                logger.warning("No webhooks found in database")
            
            return webhooks
        except Exception as e:
            logger.error(f"Error retrieving webhooks from database: {e}")
            return []

    async def get_all_bots(session: AsyncSession) -> List[Tuple[str, str, str]]:
        """Get all bot tokens and webhook URLs from the database."""
        try:
            # Query all bots with their tokens and webhook URLs
            query = select(Webhook.bot_username, Webhook.token, Webhook.webhook_url).where(Webhook.token.isnot(None))
            result = await session.execute(query)
            bots = [(row[0], row[1], row[2]) for row in result.fetchall()]
            
            logger.info(f"Retrieved {len(bots)} bots from database")
            if not bots:
                logger.warning("No bots found in database")
            
            return bots
        except Exception as e:
            logger.error(f"Error retrieving bots from database: {e}")
            return []

    @router.callback_query(F.data == "cancel_broadcast_creation")
    async def cancel_broadcast_creation(clb: CallbackQuery, state: FSMContext):
        """Cancel the broadcast creation process via button."""
        current_state = await state.get_state()
        if current_state in BroadcastForm.states:
            await state.clear()
            await clb.message.edit_text(
                "❌ <b>Создание рассылки отменено.</b>",
                parse_mode="HTML"
            )
        await clb.answer()

    async def get_all_user_ids(session: AsyncSession) -> List[int]:
        """Get all user IDs from the database."""
        query = select(Spyusers.user_id)
        result = await session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def auto_format_html(text: str) -> str:
        """Convert markdown-like syntax to HTML."""
        # Replace bold: *text* -> <b>text</b>
        text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)
        
        # Replace italic: _text_ -> <i>text</i>
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # Replace strikethrough: ~text~ -> <s>text</s>
        text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)
        
        # Replace inline code: `text` -> <code>text</code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Replace code blocks: ```text``` -> <pre>text</pre>
        text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
        
        # Replace links: [text](url) -> <a href="url">text</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # Replace headers: # Header -> <u>Header</u>
        text = re.sub(r'^# (.*?)$', r'<u>\1</u>', text, flags=re.MULTILINE)
        
        return text

    @router.message(BroadcastForm.waiting_for_message)
    async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
        """Process the message for broadcasting with auto HTML formatting."""
        # Store message details based on type
        content_type = message.content_type
        
        data = {
            "content_type": content_type,
            "buttons": []
        }
        
        # Store different content based on message type
        if content_type == ContentType.TEXT:
            # Auto-format the text to HTML
            formatted_text = await auto_format_html(message.text)
            data["text"] = formatted_text
            data["parse_mode"] = "HTML"
            
            # Also store the original text for editing purposes
            data["original_text"] = message.text
        elif content_type == ContentType.PHOTO:
            # Auto-format caption if present
            caption = message.caption or ""
            formatted_caption = await auto_format_html(caption) if caption else ""
            
            data["photo_id"] = message.photo[-1].file_id
            data["caption"] = formatted_caption
            data["original_caption"] = caption
            data["parse_mode"] = "HTML"
        elif content_type == ContentType.VIDEO:
            data["video_id"] = message.video.file_id
            data["caption"] = message.caption or ""
            data["parse_mode"] = "HTML"
        elif content_type == ContentType.DOCUMENT:
            data["document_id"] = message.document.file_id
            data["caption"] = message.caption or ""
            data["parse_mode"] = "HTML"
        elif content_type == ContentType.AUDIO:
            data["audio_id"] = message.audio.file_id
            data["caption"] = message.caption or ""
            data["parse_mode"] = "HTML"
        elif content_type == ContentType.ANIMATION:
            data["animation_id"] = message.animation.file_id
            data["caption"] = message.caption or ""
            data["parse_mode"] = "HTML"
        else:
            await message.answer(
                "❌ Этот тип сообщений не поддерживается для рассылки.\n"
                "Пожалуйста, отправьте текст, фото, видео, документ, аудио или анимацию."
            )
            return

        # Save data to state
        await state.update_data(data)
        
        # Ask if buttons should be added - add cancel button
        await message.answer(
            "✅ Сообщение для рассылки сохранено.\n\n"
            "Хотите добавить кнопки к сообщению?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="add_buttons_yes"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="add_buttons_no")
                ],
                [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast_creation")]
            ])
        )
        await state.set_state(BroadcastForm.add_buttons)

    @router.callback_query(F.data == "add_buttons_yes", BroadcastForm.add_buttons)
    async def add_buttons_yes(clb: CallbackQuery, state: FSMContext):
        """Handle adding buttons to the message."""
        await clb.message.edit_text(
            "Введите текст для кнопки:",
            parse_mode="HTML"
        )
        await state.set_state(BroadcastForm.button_text)
        await clb.answer()

    @router.callback_query(F.data == "add_buttons_no", BroadcastForm.add_buttons)
    async def add_buttons_no(clb: CallbackQuery, state: FSMContext):
        """Skip adding buttons and show preview."""
        await show_broadcast_preview(clb.message, state)
        await clb.answer()

    @router.message(BroadcastForm.button_text)
    async def process_button_text(message: Message, state: FSMContext):
        """Process button text and ask for URL."""
        button_text = message.text
        await state.update_data(current_button_text=button_text)
        
        await message.answer(
            f"Текст кнопки: <b>{button_text}</b>\n\n"
            "Теперь отправьте URL для этой кнопки:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast_creation")]
            ])
        )
        await state.set_state(BroadcastForm.button_url)

    @router.message(BroadcastForm.button_url)
    async def process_button_url(message: Message, state: FSMContext):
        """Process button URL and ask if more buttons should be added."""
        button_url = message.text
        data = await state.get_data()
        
        # Get current button text
        button_text = data.get("current_button_text")
        
        # Validate URL
        if not button_url.startswith(("http://", "https://", "tg://", "t.me/")):
            # Fix common typos
            if button_url.startswith("httos://"):
                button_url = button_url.replace("httos://", "https://")
            elif button_url.startswith("htp://"):
                button_url = button_url.replace("htp://", "http://")
            elif button_url.startswith("t.me"):
                button_url = "https://" + button_url
            else:
                # Add https:// protocol if missing
                button_url = "https://" + button_url
                
            await message.answer(
                f"⚠️ URL был исправлен на: <code>{button_url}</code>\n\n"
                "URL должен начинаться с http://, https://, tg:// или t.me/",
                parse_mode="HTML"
            )
        
        # Add button to the list
        buttons = data.get("buttons", [])
        buttons.append({"text": button_text, "url": button_url})
        
        # Update state data
        await state.update_data(buttons=buttons)
        
        # Ask if more buttons should be added - add cancel button
        await message.answer(
            f"✅ Кнопка <b>{button_text}</b> → <code>{button_url}</code> добавлена.\n\n"
            f"Всего добавлено кнопок: <b>{len(buttons)}</b>.\n\n"
            "Хотите добавить еще кнопки?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="more_buttons_yes"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="more_buttons_no")
                ],
                [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast_creation")]
            ])
        )
        await state.set_state(BroadcastForm.button_add_more)

    @router.callback_query(F.data == "more_buttons_yes", BroadcastForm.button_add_more)
    async def add_more_buttons_yes(clb: CallbackQuery, state: FSMContext):
        """Handle adding more buttons."""
        await clb.message.edit_text(
            "Введите текст для следующей кнопки:",
            parse_mode="HTML"
        )
        await state.set_state(BroadcastForm.button_text)
        await clb.answer()

    @router.callback_query(F.data == "more_buttons_no", BroadcastForm.button_add_more)
    async def add_more_buttons_no(clb: CallbackQuery, state: FSMContext):
        """Finish adding buttons and show preview."""
        await show_broadcast_preview(clb.message, state)
        await clb.answer()

    async def show_broadcast_preview(message: Message, state: FSMContext):
        """Show a preview of the broadcast message."""
        data = await state.get_data()
        content_type = data.get("content_type")
        broadcast_type = data.get("broadcast_type", "users")
        
        # Create keyboard if buttons exist
        buttons = data.get("buttons", [])
        keyboard = None
        if buttons:
            keyboard_buttons = []
            for button in buttons:
                keyboard_buttons.append([InlineKeyboardButton(
                    text=button["text"], 
                    url=button["url"]
                )])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # Send preview based on content type
        if broadcast_type == "webhooks":
            webhook_count = len(data.get("webhooks", []))
            preview_text = f"📣 <b>Предпросмотр сообщения для рассылки на {webhook_count} webhook-зеркал и пользователям:</b>\n\n"
        else:
            preview_text = "📣 <b>Предпросмотр сообщения для рассылки пользователям:</b>\n\n"
            
        await message.answer(preview_text, parse_mode="HTML")
        
        if (content_type == ContentType.TEXT):
            await message.answer(
                data["text"], 
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        elif (content_type == ContentType.PHOTO):
            await message.answer_photo(
                photo=data["photo_id"],
                caption=data["caption"],
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        elif (content_type == ContentType.VIDEO):
            await message.answer_video(
                video=data["video_id"],
                caption=data["caption"],
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        elif (content_type == ContentType.DOCUMENT):
            await message.answer_document(
                document=data["document_id"],
                caption=data["caption"],
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        elif (content_type == ContentType.AUDIO):
            await message.answer_audio(
                audio=data["audio_id"],
                caption=data["caption"],
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        elif (content_type == ContentType.ANIMATION):
            await message.answer_animation(
                animation=data["animation_id"],
                caption=data["caption"],
                parse_mode=data["parse_mode"],
                reply_markup=keyboard
            )
        
        # Show confirmation buttons
        confirm_text = "Вы уверены, что хотите отправить это сообщение "
        if broadcast_type == "webhooks":
            confirm_text += "одновременно во всех ботах всем пользователям?"
        else:
            confirm_text += "всем пользователям?"
            
        await message.answer(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
                    InlineKeyboardButton(text="🔄 Изменить", callback_data="broadcast_edit"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")
                ]
            ])
        )
        await state.set_state(BroadcastForm.confirm)

    @router.callback_query(F.data == "broadcast_confirm", BroadcastForm.confirm)
    async def confirm_broadcast(clb: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
        """Start broadcasting the message with optimized performance."""
        user_id = clb.from_user.id
        cancel_flags[user_id] = False
        
        # Get broadcast data
        data = await state.get_data()
        broadcast_type = data.get("broadcast_type", "users")
        
        if broadcast_type == "webhooks":
            # Send directly to mirror bots using their tokens instead of webhooks
            await broadcast_to_mirror_bots(clb, state, bot, session)
        else:
            # Send to users only through the main bot (default)
            await broadcast_to_users(clb, state, bot, session)
        
        await clb.answer()

    async def broadcast_to_mirror_bots(clb: CallbackQuery, state: FSMContext, main_bot: Bot, session: AsyncSession):
        user_id = clb.from_user.id
        cancel_flags[user_id] = False
        
        # Get broadcast data
        data = await state.get_data()
        
        # Get all bot tokens from database
        all_bots = await get_all_bots(session)
        total_bots = len(all_bots)
        
        if total_bots == 0:
            await clb.message.edit_text("❌ Не найдено ни одного бота для рассылки.")
            await state.clear()
            return
        
        # Create status message
        status_message = await clb.message.answer(
            "⏳ <b>Отправка через токены ботов начата...</b>\n\n"
            f"Всего ботов: <b>{total_bots}</b>\n"
            f"Прогресс: <b>0%</b> (0/{total_bots})",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
            ])
        )
        
        # Content type and buttons
        content_type = data.get("content_type")
        buttons = data.get("buttons", [])
        
        # Prepare keyboard if buttons exist
        keyboard = None
        if buttons:
            keyboard_buttons = []
            for button in buttons:
                keyboard_buttons.append([InlineKeyboardButton(
                    text=button["text"], 
                    url=button["url"]
                )])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # Create temporary folder for media
        media_path = f"temp_broadcast_{user_id}_{int(time.time())}"
        local_file_path = None

        try:
            if content_type != ContentType.TEXT:
                if not os.path.exists(media_path):
                    os.makedirs(media_path)
                try:
                    if content_type == ContentType.PHOTO:
                        file = await main_bot.get_file(data["photo_id"])
                        local_file_path = os.path.join(media_path, "photo.jpg")
                        await main_bot.download_file(file.file_path, local_file_path)
                    elif content_type == ContentType.VIDEO:
                        file = await main_bot.get_file(data["video_id"])
                        local_file_path = os.path.join(media_path, "video.mp4")
                        await main_bot.download_file(file.file_path, local_file_path)
                    elif content_type == ContentType.DOCUMENT:
                        file = await main_bot.get_file(data["document_id"])
                        local_file_path = os.path.join(media_path, "document")
                        await main_bot.download_file(file.file_path, local_file_path)
                    elif content_type == ContentType.AUDIO:
                        file = await main_bot.get_file(data["audio_id"])
                        local_file_path = os.path.join(media_path, "audio.mp3")
                        await main_bot.download_file(file.file_path, local_file_path)
                    elif content_type == ContentType.ANIMATION:
                        file = await main_bot.get_file(data["animation_id"])
                        local_file_path = os.path.join(media_path, "animation.gif")
                        await main_bot.download_file(file.file_path, local_file_path)

                except Exception as e:
                    logger.error(f"Error downloading media: {e}")
                    await status_message.edit_text(
                        f"❌ <b>Ошибка при загрузке медиафайла:</b> {str(e)}\nРассылка отменена.",
                        parse_mode="HTML"
                    )
                    if os.path.exists(media_path):
                        shutil.rmtree(media_path)
                    await state.clear()
                    return

            # Start sending through each bot token
            processed_count = 0
            successful_count = 0
            failed_count = 0
            
            # Get all user IDs
            all_user_ids = await get_all_user_ids(session)
            total_users = len(all_user_ids)

            for bot_username, bot_token, _ in all_bots:
                # Check if broadcast was canceled
                if cancel_flags.get(user_id, False):
                    break
                
                try:
                    # Create bot instance with token
                    mirror_bot = Bot(token=bot_token, session=main_bot.session)
                    logger.info(f"Created Bot instance for @{bot_username}")
                    
                    # Send message to each user ID
                    if content_type == ContentType.TEXT:
                        for uid in all_user_ids:
                            if cancel_flags.get(user_id, False):
                                break
                            try:
                                await mirror_bot.send_message(
                                    chat_id=uid,
                                    text=data["text"],
                                    parse_mode=data["parse_mode"],
                                    reply_markup=keyboard
                                )
                                successful_count += 1
                                logger.info(f"Successfully sent message to user {uid} through bot @{bot_username}")
                            except Exception as e:
                                failed_count += 1
                                logger.error(f"Error sending to user {uid} through bot @{bot_username}: {e}")
                    elif local_file_path and os.path.exists(local_file_path):
                        # Open the file once per bot
                        input_file = FSInputFile(local_file_path)
                        for uid in all_user_ids:
                            if cancel_flags.get(user_id, False):
                                break
                            try:
                                if content_type == ContentType.PHOTO:
                                    await mirror_bot.send_photo(
                                        chat_id=uid,
                                        photo=input_file,
                                        caption=data["caption"],
                                        parse_mode=data["parse_mode"],
                                        reply_markup=keyboard
                                    )
                                elif content_type == ContentType.VIDEO:
                                    await mirror_bot.send_video(
                                        chat_id=uid,
                                        video=input_file,
                                        caption=data["caption"],
                                        parse_mode=data["parse_mode"],
                                        reply_markup=keyboard
                                    )
                                elif content_type == ContentType.DOCUMENT:
                                    await mirror_bot.send_document(
                                        chat_id=uid,
                                        document=input_file,
                                        caption=data["caption"],
                                        parse_mode=data["parse_mode"],
                                        reply_markup=keyboard
                                    )
                                elif content_type == ContentType.AUDIO:
                                    await mirror_bot.send_audio(
                                        chat_id=uid,
                                        audio=input_file,
                                        caption=data["caption"],
                                        parse_mode=data["parse_mode"],
                                        reply_markup=keyboard
                                    )
                                elif content_type == ContentType.ANIMATION:
                                    await mirror_bot.send_animation(
                                        chat_id=uid,
                                        animation=input_file,
                                        caption=data["caption"],
                                        parse_mode=data["parse_mode"],
                                        reply_markup=keyboard
                                    )
                                successful_count += 1
                                logger.info(f"Successfully sent message to user {uid} through bot @{bot_username}")
                            except Exception as e:
                                failed_count += 1
                                logger.error(f"Error sending to user {uid} through bot @{bot_username}: {e}")
                    
                    # Clean up the bot instance
                    await mirror_bot.session.close()
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to create Bot instance for @{bot_username}: {e}")
                
                processed_count += 1
                
                # Update progress after each bot
                percent = round((processed_count / total_bots) * 100)
                try:
                    await status_message.edit_text(
                        f"⏳ <b>Отправка через токены ботов в процессе...</b>\n\n"
                        f"Всего ботов: <b>{total_bots}</b>\n"
                        f"Прогресс: <b>{percent}%</b> ({processed_count}/{total_bots})\n"
                        f"✓ Успешно: <b>{successful_count}</b>, ✗ Ошибок: <b>{failed_count}</b>\n\n"
                        "<i>Для отмены нажмите кнопку ниже</i>",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
                        ])
                    )
                except Exception as e:
                    logger.error(f"Error updating status: {e}")
            
            # Final status for the broadcast
            if not cancel_flags.get(user_id, False):
                await status_message.edit_text(
                    "✅ <b>Отправка через токены ботов завершена!</b>\n\n"
                    f"Всего ботов: <b>{total_bots}</b>\n"
                    f"✓ Успешно: <b>{successful_count}</b>, ✗ Ошибок: <b>{failed_count}</b>",
                    parse_mode="HTML"
                )
            else:
                await status_message.edit_text(
                    "🛑 <b>Отправка через токены ботов отменена!</b>\n\n"
                    f"Всего ботов: <b>{total_bots}</b>\n"
                    f"✓ Успешно: <b>{successful_count}</b>, ✗ Ошибок: <b>{failed_count}</b>",
                    parse_mode="HTML"
                )
            
        finally:
            if os.path.exists(media_path):
                shutil.rmtree(media_path)
            logger.info(f"Cleaned up temporary media directory: {media_path}")
            del cancel_flags[user_id]
            await state.clear()

    @router.callback_query(F.data == "broadcast_edit", BroadcastForm.confirm)
    async def edit_broadcast(clb: CallbackQuery, state: FSMContext):
        """Return to message creation step."""
        data = await state.get_data()
        broadcast_type = data.get("broadcast_type", "users")
        
        if broadcast_type == "webhooks":
            await select_webhooks_broadcast(clb, state, None)  # Pass None for session as it's not used
        else:
            await select_users_broadcast(clb, state)
    
    @router.callback_query(F.data == "broadcast_cancel", BroadcastForm.confirm)
    async def cancel_broadcast_confirm(clb: CallbackQuery, state: FSMContext):
        """Cancel broadcasting at confirmation stage."""
        await clb.message.edit_text(
            "❌ <b>Рассылка отменена.</b>",
            parse_mode="HTML"
        )
        await state.clear()
        await clb.answer()

    @router.callback_query(F.data == "cancel_broadcast")
    async def cancel_ongoing_broadcast(clb: CallbackQuery):
        """Cancel an ongoing broadcast."""
        user_id = clb.from_user.id
        if user_id in cancel_flags:
            cancel_flags[user_id] = True
            await clb.answer("Отмена рассылки... Дождитесь завершения текущей отправки.")
        else:
            await clb.answer("Нет активной рассылки для отмены.")

    return router
