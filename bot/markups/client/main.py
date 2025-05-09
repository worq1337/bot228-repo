from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

async def tut_kb() -> InlineKeyboardMarkup:
    tutorial = InlineKeyboardButton(text='❗️Тутор по установке', url='https://telegra.ph/Kak-ispolzovat-i-ustanovit-bota-01-03')
    chennel = InlineKeyboardButton(text='📰 Новостной канал', url='https://t.me/SaveMOD')
    profile = InlineKeyboardButton(text='👤 Профиль', callback_data='profile')
    create_bot = InlineKeyboardButton(text='🤖 Создать бота', callback_data='create_bot')
    row = [tutorial]
    rows = [row,[chennel],[create_bot]]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup

def help_kb(name) -> InlineKeyboardMarkup:
    bot_url = InlineKeyboardButton(text='Перейти в бота!',url=f'https://t.me/{name}')
    row = [bot_url]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup
