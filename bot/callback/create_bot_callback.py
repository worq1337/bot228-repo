import logging
from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import BotCreation

logger = logging.getLogger(__name__)

async def create_bot_callback(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession) -> None:
    """
    Handle bot creation through callback - starts the token input flow
    """
    try:
        # Answer the callback to stop loading animation
        await callback.answer()
        
        # Set state to waiting for token
        await state.set_state(BotCreation.waiting_for_token)

        # Ask user to provide token
        await callback.message.answer(
            "<b>Для создания зеркала </b><b>@SaveMod_bot</b><b> следуйте инструкции</b> 👇 \n\n"
            "<blockquote>1. Перейдите в @BotFather\n\n"
            "2. Напишите /newbot , отправьте желаемое имя бота, оно может быть абсолютно любым.\n\n"
            "3. Отправьте @Username бота. Он должен кончаться на «Bot» пример: testnetbot\n\n"
            "4. Напишите в @BotFather /mybot и выберите из списка недавно созданного бота.\n\n"
            "<b>5. Нажмите «Bot Settings», далее «Business Mod» и нажмите на «Turn on»\n\n"
            "6. «Back to Settings» -> «Back to Bot» -> «API Token» скопируйте токен и пришлите сюда.</b></blockquote>\n\n"
            "<b>Вы можете отменить операцию, отправив /cancel</b>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.exception(f"Error in create_bot callback: {e}")
        await callback.answer("An error occurred while processing your request", show_alert=True)
