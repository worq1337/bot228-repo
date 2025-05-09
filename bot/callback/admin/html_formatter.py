import re
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN


def html_router() -> Router:
    logger = logging.getLogger(__name__)
    router = Router()

    class HTMLFormatterStates(StatesGroup):
        waiting_for_text = State()

    @router.callback_query(F.data == "format_html")
    async def start_html_formatter(clb: CallbackQuery, state: FSMContext):
        """Start the HTML formatting process."""
        if clb.from_user.id not in ADMIN:
            await clb.answer("Доступ запрещен", show_alert=True)
            return
        
        await clb.message.edit_text(
            "🔠 <b>HTML Форматирование</b>\n\n"
            "Отправьте текст для форматирования в HTML. Поддерживаются следующие правила:\n\n"
            "• <b>Жирный текст</b>\n"
            "• <i>Курсив</i>\n"
            "• <u>Подчеркнутый</u>\n"
            "• <s>Зачеркнутый</s>\n"
            "• <code>Моноширинный шрифт</code>\n"
            "• <pre>Блок кода</pre>\n"
            "• Ссылки\n\n"
            "Просто отформатируйте текст в Telegram, и система автоматически преобразует его в HTML.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_html_format")],
                [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_admin_pnl")]
            ])
        )
        
        await state.set_state(HTMLFormatterStates.waiting_for_text)
        await clb.answer()

    @router.callback_query(F.data == "cancel_html_format", HTMLFormatterStates.waiting_for_text)
    async def cancel_html_format_callback(clb: CallbackQuery, state: FSMContext):
        """Cancel HTML formatting via button."""
        await state.clear()
        await clb.message.edit_text(
            "❌ <b>Форматирование отменено.</b>",
            parse_mode="HTML"
        )
        await clb.answer()

    @router.message(Command("cancel"), HTMLFormatterStates.waiting_for_text)
    async def cancel_formatting(message: Message, state: FSMContext):
        """Cancel the HTML formatting process."""
        current_state = await state.get_state()
        if current_state == HTMLFormatterStates.waiting_for_text:
            await state.clear()
            await message.answer("❌ Форматирование отменено.")

    @router.message(HTMLFormatterStates.waiting_for_text)
    async def process_text_for_formatting(message: Message, state: FSMContext):
        """Process the message and convert its entities to HTML."""
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение.")
            return
        
        try:
            # If message has entities, use them for HTML formatting
            if message.entities:
                formatted_text = await convert_entities_to_html(message.text, message.entities)
            else:
                # If no entities, try to format using regex patterns
                formatted_text = format_to_html(message.text)
            
            # Send the formatted text as preview
            await message.answer(
                "📄 <b>Предпросмотр отформатированного текста:</b>",
                parse_mode="HTML"
            )
            
            # Send the formatted text with HTML parsing
            await message.answer(
                formatted_text,
                parse_mode="HTML"
            )
            
            # Send the raw HTML code as plain text without HTML parsing
            # This ensures the code is displayed as-is
            code_display = f"📝 HTML-код:\n\n{formatted_text}"
            await message.answer(code_display)
            
            # Success message and options
            await message.answer(
                "✅ <b>Текст успешно отформатирован!</b>\n\n"
                "Вы можете скопировать HTML-код выше и использовать его в рассылке.\n"
                "Для форматирования другого текста, просто отправьте его.\n"
                "Для выхода отправьте /cancel.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.exception(f"Error formatting text: {e}")
            await message.answer(
                f"❌ <b>Ошибка при форматировании:</b>\n\n{str(e)}\n\n"
                "Проверьте правильность синтаксиса и попробуйте снова.",
                parse_mode="HTML"
            )

    async def convert_entities_to_html(text: str, entities: list[MessageEntity]) -> str:
        """Convert Telegram message entities to HTML formatted text."""
        # Dictionaries for inserting opening and closing tags by positions in the text
        openings = {}
        closings = {}
        
        # Sort entities by offset (usually they are already sorted)
        sorted_entities = sorted(entities, key=lambda e: e.offset)
        for entity in sorted_entities:
            offset = entity.offset
            length = entity.length
            end = offset + length
            
            # Determine opening and closing tags depending on entity type
            if entity.type == "bold":
                open_tag, close_tag = "<b>", "</b>"
            elif entity.type == "italic":
                open_tag, close_tag = "<i>", "</i>"
            elif entity.type == "underline":
                open_tag, close_tag = "<u>", "</u>"
            elif entity.type == "strikethrough":
                open_tag, close_tag = "<s>", "</s>"
            elif entity.type == "code":
                open_tag, close_tag = "<code>", "</code>"
            elif entity.type == "pre":
                open_tag, close_tag = "<pre>", "</pre>"
            elif entity.type == "text_link" and entity.url:
                open_tag, close_tag = f'<a href="{entity.url}">', "</a>"
            else:
                # Skip unsupported entity types
                continue

            # Save tags for insertion at the right positions
            openings.setdefault(offset, []).append(open_tag)
            closings.setdefault(end, []).append(close_tag)

        # Build the final text
        result = ""
        for i in range(len(text) + 1):
            # Insert closing tags if needed before the character
            if i in closings:
                for tag in reversed(closings[i]):
                    result += tag
            if i < len(text):
                # Insert opening tags if needed before the character
                if i in openings:
                    for tag in openings[i]:
                        result += tag
                result += text[i]
        return result

    # Keep the original regex-based formatter as a fallback
    def format_to_html(text: str) -> str:
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

    def escape_html(text: str) -> str:
        """Escape HTML characters for display in HTML code."""
        return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')

    def escape_markdown(text: str) -> str:
        """Escape special characters for Markdown V2."""
        escape_chars = '_*[]()~`>#+-=|{}.!'
        return "".join(f"\\{c}" if c in escape_chars else c for c in text)
    
    return router
