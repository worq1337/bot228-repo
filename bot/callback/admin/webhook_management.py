import logging
from typing import List

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery, 
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db import Webhook
from config import ADMIN

logger = logging.getLogger(__name__)
router = Router()

# FSM States for webhook management
class WebhookForm(StatesGroup):
    waiting_for_url = State()      # Waiting for webhook URL
    confirm_delete = State()       # Confirm webhook deletion

@router.callback_query(F.data == "manage_webhooks")
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

@router.callback_query(F.data == "add_webhook")
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

@router.message(WebhookForm.waiting_for_url)
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

@router.callback_query(F.data.startswith("delete_webhook_"))
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

@router.callback_query(F.data == "confirm_webhook_delete", WebhookForm.confirm_delete)
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

@router.callback_query(F.data == "cancel_webhook_delete")
async def cancel_webhook_delete(clb: CallbackQuery, state: FSMContext):
    """Cancel webhook deletion."""
    await state.clear()
    await manage_webhooks(clb, None)  # Pass None for session as it will be injected
    await clb.answer()

@router.callback_query(F.data == "cancel_webhook_add")
async def cancel_webhook_add(clb: CallbackQuery, state: FSMContext):
    """Cancel webhook addition."""
    await state.clear()
    await manage_webhooks(clb, None)  # Pass None for session as it will be injected
    await clb.answer()

async def get_all_webhooks(session: AsyncSession) -> List[str]:
    """Get all webhook URLs from the database."""
    query = select(Webhook.webhook_url)
    result = await session.execute(query)
    return [row[0] for row in result.fetchall()]
