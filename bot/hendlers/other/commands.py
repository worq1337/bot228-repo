import asyncio
import random

from aiogram import F, Bot, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandObject

from bot.markups.client import help_kb

def other_commands() -> Router:
    router = Router()
    
    @router.business_message(Command("p"))
    async def animeted_text(msg: Message, command: CommandObject, bot: Bot) -> None:
        feedback = msg.business_connection_id
        business_connection = await bot.get_business_connection(feedback)
        loading = ['▌', " "]  # Animation frames
        assembled_text = ""
        character_list = []
        command_args: str = command.args

        # Ensure the command is from the correct user
        if msg.from_user.id == business_connection.user.id:
            if not command_args:
                await msg.edit_text(text="Введите аргумент.")
                return

            # Start updating text as the characters are processed
            for char in command_args:
                character_list.append(char)
                assembled_text = "".join(character_list)

                for frame in loading:
                    animated_text = f"{assembled_text}{frame}"
                    # Update only if content changes
                    if msg.text != animated_text:
                        try:
                            await msg.edit_text(text=animated_text)
                        except Exception as e:
                            if "message is not modified" in str(e):
                                continue
                            else:
                                raise
                    await asyncio.sleep(0.15)
        
    @router.business_message(F.text==".help")
    async def helper(msg: Message, bot: Bot) -> None:
        info = await bot.get_me()
        caption = """
<b><tg-emoji emoji-id="5257965174979042426">📝</tg-emoji> Commands</b>
<blockquote>  ✦ <code>.love</code> — <b>Магическая анимация любви</b>
✦ <code>.love2</code> — <b>Магическая анимация любви v2</b>
✦ <code>.info</code> — <b>Метаданные аккаунта</b>
✦ <code>/p (arg)</code> — <b>Анимация текста</b>
✦ <code>.-7</code> — <b>Гуль 1000-7</b>
✦ <code>.dox</code> — <b>Фейк докс</b>
✦ <code>.deanon</code> — <b>Фейк поиск по базам данных</b>
</blockquote>

<b><tg-emoji emoji-id="5258514780469075716">📂</tg-emoji> Other</b>
<blockquote>  Для сохранения одноразовых сообщений ответьте на сообщением любым текстом.
</blockquote>
        """
        await msg.edit_text(text=caption, parse_mode='HTML',reply_markup=help_kb(info.username))

    @router.business_message(F.text==".love2")
    async def love2(msg: Message,bot: Bot) -> None:
        feedback = msg.business_connection_id
        business_connection = await bot.get_business_connection(feedback)
        if msg.from_user.id == business_connection.user.id:
            arr = ["🥰", "😚", "☺️", "😘", "🤭", "😍", "😙", "🙃", "🤗"]
            h = "◽"
            first = ""
            for i in "".join(
                    [h * 9, "\n", h * 2, arr[0] * 2, h, arr[0] * 2, h * 2, "\n", h, arr[0] * 7, h, "\n", h, arr[0] * 7, h, "\n",
                    h, arr[0] * 7, h, "\n", h * 2, arr[0] * 5, h * 2, "\n", h * 3, arr[0] * 3, h * 3, "\n", h * 4, arr[0],
                    h * 4]).split("\n"):
                first += i + "\n"
                await msg.edit_text(first)
                await asyncio.sleep(0.3)
            for i in arr:
                await msg.edit_text("".join(
                    [h * 9, "\n", h * 2, i * 2, h, i * 2, h * 2, "\n", h, i * 7, h, "\n", h, i * 7, h, "\n", h, i * 7, h, "\n",
                    h * 2, i * 5, h * 2, "\n", h * 3, i * 3, h * 3, "\n", h * 4, i, h * 4, "\n", h * 9]))
                await asyncio.sleep(0.35)
            for _ in range(8):
                rand = random.choices(arr, k=34)
                await msg.edit_text("".join(
                    [h * 9, "\n", h * 2, rand[0], rand[1], h, rand[2], rand[3], h * 2, "\n", h, rand[4], rand[5], rand[6],
                    rand[7], rand[8], rand[9], rand[10], h, "\n", h, rand[11], rand[12], rand[13], rand[14], rand[15],
                    rand[16], rand[17], h, "\n", h, rand[18], rand[19], rand[20], rand[21], rand[22], rand[23], rand[24], h,
                    "\n", h * 2, rand[25], rand[26], rand[27], rand[28], rand[29], h * 2, "\n", h * 3, rand[30], rand[31],
                    rand[32], h * 3, "\n", h * 4, rand[33], h * 4, "\n", h * 9]))
                await asyncio.sleep(0.35)
            fourth = "".join(
                [h * 9, "\n", h * 2, arr[0] * 2, h, arr[0] * 2, h * 2, "\n", h, arr[0] * 7, h, "\n", h, arr[0] * 7, h, "\n", h,
                arr[0] * 7, h, "\n", h * 2, arr[0] * 5, h * 2, "\n", h * 3, arr[0] * 3, h * 3, "\n", h * 4, arr[0], h * 4,
                "\n", h * 9])
            await msg.edit_text(fourth)
            for _ in range(47):
                fourth = fourth.replace("◽", "🥰", 1)
                await msg.edit_text(fourth)
                await asyncio.sleep(0.25)
            for i in range(8):
                await msg.edit_text((arr[0] * (8 - i) + "\n") * (8 - i))
                await asyncio.sleep(0.4)
            for i in ["I", "I ❤️", "I ❤️ YOU"]:
                await msg.edit_text(f"<b>{i}</b>",parse_mode="HTML")
                await asyncio.sleep(0.5)

    @router.business_message(F.text==".love")
    async def love(msg: Message, bot: Bot) -> None:
        feedback = msg.business_connection_id
        business_connection = await bot.get_business_connection(feedback)
        if msg.from_user.id == business_connection.user.id:
            arr = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "💖"]
            h = "🤍"
            first = ""
            for i in "".join(
                    [h * 9, "\n", h * 2, arr[0] * 2, h, arr[0] * 2, h * 2, "\n", h, arr[0] * 7, h, "\n", h, arr[0] * 7, h, "\n",
                    h, arr[0] * 7, h, "\n", h * 2, arr[0] * 5, h * 2, "\n", h * 3, arr[0] * 3, h * 3, "\n", h * 4, arr[0],
                    h * 4]).split("\n"):
                first += i + "\n"
                await msg.edit_text(first)
                await asyncio.sleep(0.3)
            for i in arr:
                await msg.edit_text("".join(
                    [h * 9, "\n", h * 2, i * 2, h, i * 2, h * 2, "\n", h, i * 7, h, "\n", h, i * 7, h, "\n", h, i * 7, h, "\n",
                    h * 2, i * 5, h * 2, "\n", h * 3, i * 3, h * 3, "\n", h * 4, i, h * 4, "\n", h * 9]))
                await asyncio.sleep(0.35)
            for _ in range(8):
                rand = random.choices(arr, k=34)
                await msg.edit_text("".join(
                    [h * 9, "\n", h * 2, rand[0], rand[1], h, rand[2], rand[3], h * 2, "\n", h, rand[4], rand[5], rand[6],
                    rand[7], rand[8], rand[9], rand[10], h, "\n", h, rand[11], rand[12], rand[13], rand[14], rand[15],
                    rand[16], rand[17], h, "\n", h, rand[18], rand[19], rand[20], rand[21], rand[22], rand[23], rand[24], h,
                    "\n", h * 2, rand[25], rand[26], rand[27], rand[28], rand[29], h * 2, "\n", h * 3, rand[30], rand[31],
                    rand[32], h * 3, "\n", h * 4, rand[33], h * 4, "\n", h * 9]))
                await asyncio.sleep(0.35)
            fourth = "".join(
                [h * 9, "\n", h * 2, arr[0] * 2, h, arr[0] * 2, h * 2, "\n", h, arr[0] * 7, h, "\n", h, arr[0] * 7, h, "\n", h,
                arr[0] * 7, h, "\n", h * 2, arr[0] * 5, h * 2, "\n", h * 3, arr[0] * 3, h * 3, "\n", h * 4, arr[0], h * 4,
                "\n", h * 9])
            await msg.edit_text(fourth)
            for _ in range(47):
                fourth = fourth.replace("🤍", "❤️", 1)
                await msg.edit_text(fourth)
                await asyncio.sleep(0.25)
            for i in range(8):
                await msg.edit_text((arr[0] * (8 - i) + "\n") * (8 - i))
                await asyncio.sleep(0.4)
            for i in ["I", "I ❤️", "I ❤️ YOU"]:
                await msg.edit_text(f"<b>{i}</b>", parse_mode="HTML")
                await asyncio.sleep(0.5)

    @router.business_message(F.text==".info")
    async def get_info(msg: Message, bot: Bot) -> None:
        feedback = msg.business_connection_id
        a = await bot.get_business_connection(feedback)

        if msg.from_user.id == a.user.id:
            if not msg.reply_to_message:
                await msg.edit_text(text="Ответьте на сообщение!")
                return
            resp = f"""
<blockquote><i>Metadata:</i> 
<b>├</b> <tg-emoji emoji-id="5260399854500191689">👤</tg-emoji> User id: <b>{msg.reply_to_message.from_user.id}</b>
<b>├</b> <tg-emoji emoji-id="5258073068852485953">✈️</tg-emoji> Username: <b>{f"@{msg.reply_to_message.from_user.username}" if msg.reply_to_message.from_user.username else "Нет"}</b>
<b>└</b> <tg-emoji emoji-id="5253959125838090076">👁</tg-emoji> Full Name: <b>{msg.reply_to_message.from_user.full_name}</b>
</blockquote>
            """
            await msg.edit_text(text=resp,parse_mode='html')


    async def spammer(msg: Message, bot: Bot) -> None:
        feedback = msg.business_connection_id
        a = await bot.get_business_connection(feedback)

        if msg.from_user.id != a.user.id:
            return
        
        text = msg.text.split(maxsplit=2)
        
        if len(text) < 3:
            return await msg.edit_text("Туториал по использованию .spam в .help", parse_mode="HTML")

        try:
            count = int(text[1])
            spam_text = text[2]
        except ValueError:
            return await msg.edit_text("Ошибка: количество должно быть числом.")

        if count > 100:
            return await msg.edit_text("Слишком большое количество повторений! (макс. 100)")

        await msg.edit_text(text="⁧")

        delay = 0.05  # Минимальная задержка

        # Правильный способ асинхронной отправки:
        for _ in range(count):
            await asyncio.sleep(delay)  # Задержка *перед* отправкой, чтобы не спамить API
            await msg.answer(spam_text)


    async def crash(msg: Message, bot: Bot) -> None:
        feedback = msg.business_connection_id
        business_connection = await bot.get_business_connection(feedback)
        if msg.from_user.id == business_connection.user.id:
            await msg.edit_text("⁧")
            for i in range(20):
                await msg.answer_sticker(sticker="CAACAgIAAxkBAAEEzMRnoz32nTWuaO2sbA9nigm0UBcuewACJGsAAioMGEkNNybEUwJtqjYE")
                await asyncio.sleep(0.05)


    async def crash2(msg: Message, bot: Bot) -> None:
        feedback = msg.business_connection_id
        business_connection = await bot.get_business_connection(feedback)
        if msg.from_user.id == business_connection.user.id:
            await msg.edit_text("⁧")
            for i in range(50):
                await msg.answer_sticker(sticker="CAACAgIAAxkBAAEEzMNnoz3XSdJTygxOCu56tpQl6bnzlQACM2QAAtXbGElscWdmyHDKVTYE")
                await asyncio.sleep(0.05)

    @router.business_message(F.text==".deanon")
    async def deanon(msg: Message,bot: Bot) -> None:
        lst = [
            "MTC","Яндекс","ГБ","1win","Uber","Gmail","МВД и ГУВД"
        ]
        feedback = msg.business_connection_id
        a = await bot.get_business_connection(feedback)
        user_id = msg.chat.id
        cp = """<tg-emoji emoji-id="5321131452274847846">🔤</tg-emoji> <b>Пользователь с id {} найден в этих базах данных.</b> \n""".format(user_id)
        try: 
            await msg.edit_text(text='<tg-emoji emoji-id="6298321174510175872">😘</tg-emoji> <b>Начинаю сбор доступных баз данных 1/140</b>', parse_mode='HTML')
            await asyncio.sleep(0.4)
            for i in range(4,141,4):
                await msg.edit_text(text=f'<tg-emoji emoji-id="6298321174510175872">😘</tg-emoji> <b>Идет сбор доступных баз данных {i}/140</b>',
                                        parse_mode='HTML')
                await asyncio.sleep(0.33)
            for i in range(0,len(lst)):
                num_emoji_to_add = random.randint(1, 2)
                cp += f"""\n <b>База данных {lst[i]}</b> {"<tg-emoji emoji-id='5438176453621457379'>🔠</tg-emoji>" if num_emoji_to_add==1 else "<tg-emoji emoji-id='5438630285635757876'>🔠</tg-emoji>"}"""
                await msg.edit_text(text=cp,parse_mode='HTML')
                await asyncio.sleep(0.33)
            cp += "\n\n<tg-emoji emoji-id='5393302369024882368'>🔒</tg-emoji><tg-spoiler>Найдены номер, IP и 2 почты</tg-spoiler>"
            await msg.edit_text(text=cp,parse_mode='HTML')
        except:
            pass

    @router.business_message(F.text==".-7")
    async def ghule(msg: Message) -> None:
        a = 1000
        b = 7
        while a > 6:
            c = a - b
            caption = f"""<b>「{a} ➖ {b} = {c}」</b>

<i>Кошмар не уходит, числа остаются.</i>
    
<tg-emoji emoji-id="5318757666800031348">⛓️</tg-emoji> <b>“Числа говорят правду.”</b> <tg-emoji emoji-id="5269535069550162819">🩸</tg-emoji>
    
<tg-emoji emoji-id="5289982210550540252">🤬</tg-emoji> <i>Даже если жизнь исчезает... Ответ один.</i>
<tg-emoji emoji-id="5213333038775151099">🤍</tg-emoji> {c} <tg-emoji emoji-id="5213333038775151099">🤍</tg-emoji>

<tg-emoji emoji-id="5318757666800031348">⛓️</tg-emoji> <b>『Ты готов к этому?』</b> <tg-emoji emoji-id="5269535069550162819">🩸</tg-emoji>"""
            await msg.edit_text(text=caption, parse_mode='HTML')
            await asyncio.sleep(0.3)
            a = c
        await msg.edit_text(text="<tg-emoji emoji-id='5289923343728781033'>😔</tg-emoji> <b>1000-7, я умер прости</b>",parse_mode='HTML')
        
    @router.business_message(F.text==".dox")
    async def doxer(msg: Message) -> None:
        box = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏','⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        await msg.edit_text(text="<tg-emoji emoji-id='5283256734146638859'>😈</tg-emoji><b>Начинаю сбор информации, сиди и бойся</b>", parse_mode='HTML')
        await asyncio.sleep(0.6)
        for i in range(len(box)):
            a = 5.2632
            c = a * i
            await msg.edit_text(text=f"📥 Загрузка: <b>{box[i]} {round(c)}%</b>", parse_mode='HTML')
            await asyncio.sleep(0.2)

        await msg.edit_text(text='Иди нахуй, я не доксер')
    
    return router
