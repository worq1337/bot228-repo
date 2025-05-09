import asyncio
import logging
from typing import Any

from aiogram import Router, Bot, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandStart, CommandObject

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Spyusers
from bot.markups.client import tut_kb

from bot.utils.check import is_bot_token
from bot.utils.creat import command_add_bot

def start_router() -> Router:
    router = Router()
    logger = logging.getLogger(__name__)

    @router.message(CommandStart())
    async def start(
            message: Message,
            session: AsyncSession,
            bot: Bot,
            command: CommandObject = None
        ) -> Any:
        
        try:
            # Get referral code from command args
            bot_name = await bot.get_me()
            b_check = bot_name.can_connect_to_business
            ref_id = command.args if command and command.args else ""
            user_id = message.from_user.id
            
            logger.info(f"Start command received with args: {ref_id}")
            
            # Check if user exists in database
            user = await session.scalar(select(Spyusers).where(Spyusers.user_id == user_id))
            
            send_caption = f"""
<b>👋 Добро пожаловать.</b>

<b>🕵️ {bot_name.full_name}</b> - позволит тебе все что можно и нельзя. С гарантией на полную безопастность акаунта и конфиденциальность. 

Коротко нашем функционале 👇 
<blockquote>• Сохранять одноразовые видео/фото/кружки и голосовые.
• Сохранять видео/фото с таймером. 
• Сохранять удаленные и отредактированные сообщения. 
• Делать крутые анимации.</blockquote> 
<b>Скорее читай инструкцию👇</b>
"""
            # Prepare image
            registration_image_path = "images/logo.jpg"
            registration_photo = FSInputFile(registration_image_path)
            
            # Handle new user registration
            if user is None:
                new_user = Spyusers(user_id=user_id)
                
                # Add referral if provided
                if ref_id:
                    # Make sure the referral ID is valid (numeric)
                    try:
                        ref_user_id = int(ref_id)
                        new_user.ref_id = ref_user_id
                        logger.info(f"New user {user_id} registered with referrer: {ref_user_id}")
                        
                        # Optionally: check if referrer exists and update their stats
                        referrer = await session.scalar(select(Spyusers).where(Spyusers.user_id == ref_user_id))
                        if referrer:
                            # If you have a referral count column, you could increment it here
                            # referrer.referrals_count += 1
                            logger.info(f"Referrer {ref_user_id} found and updated")
                    except ValueError:
                        logger.warning(f"Invalid referral ID: {ref_id}")
                
                session.add(new_user)
                logger.info(f"New user registered: {user_id}")
                
                # Send welcome message with photo
                if b_check:
                    await message.answer_photo(
                        photo=registration_photo,
                        caption=send_caption,
                        parse_mode='HTML',
                        reply_markup=await tut_kb()
                    )
                else:
                    await message.answer(
                        text="У бота нет доступа к бизнес сообщениям\n"
                        "Включити её в настройках бота"
                                         )
            else:
                # User already exists
                logger.info(f"Existing user: {user_id}")
                if b_check:
                    await message.answer_photo(
                        photo=registration_photo,
                        caption=send_caption,
                        parse_mode='HTML',
                        reply_markup=await tut_kb()
                    )
                else: 
                    await message.answer(
                        text="У бота нет доступа к бизнес сообщениям\n"
                        "Включити её в настройках бота"
                                         )


        except Exception as ex:
            logger.exception(f"Error in start handler: {ex}")
        finally:
            await asyncio.sleep(0.09)  # Small delay as in original code
            

    @router.message(Command("add", magic=F.args.func(is_bot_token)))
    async def add(message: Message, bot: Bot, token: str) -> Any:
        return await command_add_bot(message, bot, token)
    
    return router
