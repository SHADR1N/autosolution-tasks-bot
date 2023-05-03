import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor
from aiogram import types

from addons_bot.handler_bot import Handler

load_dotenv()

API_TOKEN = os.environ.get("TOKEN_BOT")

handler = Handler()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler()
async def message_simple(message: types.Message):
    uid = message.from_user.id
    mid = message.message_id
    command = message.text

    if await handler.answer(bot, uid, mid, command):
        return

    return await message.answer("Не известная команад.")


def start_bot():
    executor.start_polling(dp, skip_updates=True)
