import logging
import tempfile
import os
from typing import List

from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db import Spyusers, Webhook
from config import ADMIN

from bot.markups.admin import status_kb, admin_kb

logger = logging.getLogger(__name__)

class WebhookForm(StatesGroup):
    waiting_for_url = State()      # Waiting for webhook URL
    confirm_delete = State()       # Confirm webhook deletion

async def full_status(clb: CallbackQuery, session: AsyncSession):
    """Get and display total user count from database."""
    try:
        # Count users in database
        query = select(func.count()).select_from(Spyusers)
        total_users = await session.scalar(query)
        
        # Display the information
        await clb.message.edit_text(
            text=f'Количество пользователей в базе: <b>{total_users}</b>',
            parse_mode="HTML",
            reply_markup=await status_kb()
        )
        
        logger.info(f"Admin {clb.from_user.id} requested user count: {total_users}")
        await clb.answer()
        
    except Exception as e:
        logger.exception(f"Error fetching user count: {e}")
        await clb.message.answer("Ошибка при получении статистики.")
        await clb.answer("Произошла ошибка")

async def get_all_users(clb: CallbackQuery, session: AsyncSession):
    """Generate a text file with all user IDs and send it to admin."""
    tmp_path = None
    
    try:
        # Check if user is admin
        if clb.from_user.id not in ADMIN:
            await clb.answer("Доступ запрещен", show_alert=True)
            return

        # Query all users from database
        query = select(Spyusers.user_id)
        result = await session.execute(query)
        all_users = [str(row[0]) for row in result.fetchall()]
        
        # Create a temporary file with context manager
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
            tmp.write(f"Всего пользователей: {len(all_users)}\n\n")
            tmp.write("Список ID пользователей:\n")
            for i, user_id in enumerate(all_users, 1):
                tmp.write(f"{i}. {user_id}\n")
            tmp_path = tmp.name
            logger.info(f"Created temporary file at {tmp_path}")
        
        # Send the file
        file = FSInputFile(tmp_path, filename=f"users_list_{len(all_users)}.txt")
        await clb.message.answer_document(
            document=file, 
            caption=f"📊 Список всех {len(all_users)} пользователей бота"
        )
        
        logger.info(f"Admin {clb.from_user.id} exported all {len(all_users)} user IDs")
        await clb.answer()
        
    except Exception as e:
        logger.exception(f"Error exporting user list: {e}")
        await clb.message.answer("Ошибка при получении списка пользователей.")
        await clb.answer("Произошла ошибка")
    
    finally:
        # Always delete the temporary file if it was created
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Temporary file {tmp_path} deleted successfully")
            except Exception as e:
                logger.error(f"Failed to delete temporary file {tmp_path}: {e}")


async def back_admin_panel(clb: CallbackQuery, session: AsyncSession):
    """Return to admin panel from other admin screens."""
    try:
        if clb.from_user.id not in ADMIN:
            await clb.answer("Доступ запрещен", show_alert=True)
            return
        
        caption = "<b><u>Добро пожаловать в админ панель!</u></b>\n"\
                 f"<blockquote><b>🆔 Ваш ID:</b> <i><code>{clb.from_user.id}</code></i>\n"\
                 f"<b>👤 Ваше имя:</b> <i>{clb.from_user.full_name}</i>\n"\
                 f"<b>👨🏻‍💻 Ваш username:</b> <i>@{clb.from_user.username}</i></blockquote>"
        
        # Edit the current message to show admin panel
        await clb.message.edit_text(
            text=caption,
            parse_mode='HTML',
            reply_markup=await admin_kb()
        )
        
        logger.info(f"Admin {clb.from_user.id} returned to admin panel")
        await clb.answer()
        
    except Exception as e:
        logger.exception(f"Error showing admin panel: {e}")
        await clb.answer("Произошла ошибка", show_alert=True)

async def get_all_webhooks(session: AsyncSession) -> List[str]:
    """Get all webhook URLs from the database."""
    query = select(Webhook.webhook_url)
    result = await session.execute(query)
    return [row[0] for row in result.fetchall()]

async def manage_webhooks(clb: CallbackQuery, session: AsyncSession):
    """Show webhook management menu."""
    if clb.from_user.id not in ADMIN:
        await clb.answer("Доступ запрещен", show_alert=True)
        return
    
    # Get list of webhooks from database
    webhooks = await get_all_webhooks(session)
    
    # Create reply markup with options
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить webhook", callback_data="add_webhook")]
    ]
    
    # Add list of existing webhooks with delete buttons
    webhook_text = ""
    for i, url in enumerate(webhooks, 1):
        webhook_text += f"{i}. <code>{url}</code>\n"
        keyboard.append([InlineKeyboardButton(text=f"❌ Удалить {i}", callback_data=f"delete_webhook_{i}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin_pnl")])
    
    message_text = "📡 <b>Управление webhook-зеркалами</b>\n\n"
    if webhook_text:
        message_text += f"Текущие webhook URLs:\n{webhook_text}"
    else:
        message_text += "Нет настроенных webhook URLs."
    
    await clb.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await clb.answer()

async def add_webhook(clb: CallbackQuery, state: FSMContext):
    """Start the webhook addition process."""
    if clb.from_user.id not in ADMIN:
        await clb.answer("Доступ запрещен", show_alert=True)
        return
    
    await clb.message.edit_text(
        "📝 <b>Добавление webhook URL</b>\n\n"
        "Отправьте URL для webhook-зеркала.\n"
        "URL должен начинаться с http:// или https://",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_webhook_add")]
        ])
    )
    await state.set_state(WebhookForm.waiting_for_url)
    await clb.answer()

async def process_webhook_url(message: Message, state: FSMContext, session: AsyncSession):
    """Process the webhook URL."""
    url = message.text.strip()
    
    # Validate URL
    if not url.startswith(("http://", "https://")):
        # Try to fix common issues
        if url.startswith("www."):
            url = "https://" + url
        else:
            await message.answer(
                "❌ Неверный формат URL. URL должен начинаться с http:// или https://.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ Попробовать снова", callback_data="add_webhook")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_webhook_add")]
                ])
            )
            return
    
    # Add webhook to database
    new_webhook = Webhook(webhook_url=url)
    session.add(new_webhook)
    await session.commit()
    
    await message.answer(
        f"✅ <b>Webhook добавлен успешно!</b>\n\n"
        f"URL: <code>{url}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[

            [InlineKeyboardButton(text="⬅️ Назад к управлению", callback_data="manage_webhooks")]
        ])
    )
    await state.clear()

async def delete_webhook_confirm(clb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm webhook deletion."""
    if clb.from_user.id not in ADMIN:
        await clb.answer("Доступ запрещен", show_alert=True)
        return
    
    # Extract index from callback data
    index = int(clb.data.replace("delete_webhook_", ""))
    
    # Get webhook URL
    webhooks = await get_all_webhooks(session)
    if index <= 0 or index > len(webhooks):
        await clb.answer("Webhook не найден", show_alert=True)
        return
    
    webhook_url = webhooks[index - 1]
    await state.update_data(webhook_url=webhook_url)
    
    await clb.message.edit_text(
        f"❓ <b>Подтвердите удаление</b>\n\n"
        f"Вы уверены, что хотите удалить webhook:\n"
        f"<code>{webhook_url}</code>?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_webhook_delete"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_webhook_delete")
            ]
        ])
    )
    await state.set_state(WebhookForm.confirm_delete)
    await clb.answer()

async def delete_webhook(clb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Delete the webhook."""
    data = await state.get_data()
    webhook_url = data.get("webhook_url")
    
    # Delete webhook from database
    await session.execute(delete(Webhook).where(Webhook.webhook_url == webhook_url))
    await session.commit()
    
    await clb.message.edit_text(
        f"✅ <b>Webhook удален</b>\n\n"
        f"URL: <code>{webhook_url}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_webhooks")]
        ])
    )
    await state.clear()
    await clb.answer()

async def cancel_webhook_delete(clb: CallbackQuery, state: FSMContext):
    """Cancel webhook deletion."""
    await state.clear()
    await manage_webhooks(clb, None)  # Pass None for session as it will be injected
    await clb.answer()

async def cancel_webhook_add(clb: CallbackQuery, state: FSMContext):
    """Cancel webhook addition."""
    await state.clear()
    await manage_webhooks(clb, None)  # Pass None for session as it will be injected
    await clb.answer()


