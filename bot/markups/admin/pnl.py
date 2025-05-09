from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

async def admin_kb() -> InlineKeyboardMarkup:
    boardcase = InlineKeyboardButton(text='📢 Рассылка', callback_data='board')
    status = InlineKeyboardButton(text='📊 Статистика', callback_data='full_status')
    html = InlineKeyboardButton(text='🔠 Форматировать HTML', callback_data='format_html')
    rows = [
        [boardcase],
        [status],
        [html]
    ]    
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup


async def board_kb() -> InlineKeyboardMarkup:
    check = InlineKeyboardButton(text='👁 Проверить', callback_data='board_check')
    add_btn = InlineKeyboardButton(text='➕ Добавить', callback_data='board_add')
    cancel = InlineKeyboardButton(text='❌ Отмена', callback_data='board_cancel')
    rows = [
        [check, add_btn],
        [cancel]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup


async def status_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text='📄 Получить .txt', callback_data='get_all_users')],
        [InlineKeyboardButton(text='⬅️ Наузад', callback_data='back_admin_pnl')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup
