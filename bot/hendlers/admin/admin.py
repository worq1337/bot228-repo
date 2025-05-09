from typing import Any

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Spyusers
from config import ADMIN

from bot.markups.admin import admin_kb

def admin_router() -> Router:
    router = Router()

    @router.message(Command("admin"))
    async def admin(message: Message, session: AsyncSession) -> Any:
        caption = "<b><u>Добро пожаловать в админ панель!</u></b>\n"\
                f"<blockquote><b>🆔 Ваш ID:</b> <i><code>{message.from_user.id}</code></i>\n"\
                f"<b>👤 Ваше имя:</b> <i>{message.from_user.full_name}</i>\n"\
                f"<b>👨🏻‍💻 Ваш username:</b> <i>@{message.from_user.username}</i></blockquote>"
        if message.from_user.id in ADMIN:
            await message.answer(text=caption,parse_mode='HTML',reply_markup=await admin_kb())
            

    return router
