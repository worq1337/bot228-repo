
from aiogram.fsm.state import State, StatesGroup

class BotCreation(StatesGroup):
    waiting_for_token = State()
