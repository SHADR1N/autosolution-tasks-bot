from aiogram import Bot
from aiogram import types

from .commands import command_answer


class Handler:
    def __init__(self):
        ...

    @staticmethod
    async def text_keyboard(buttons: list, row_width: int = 2) -> types.ReplyKeyboardMarkup:
        knb = types.ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=True)
        for button in buttons:
            knb.add(
                *[types.KeyboardButton(text=text) for text in button]
            )
        return knb

    @staticmethod
    async def inline_keyboard(buttons: list, row_width: int = 2) -> types.InlineKeyboardMarkup:
        knb = types.InlineKeyboardMarkup(row_width=row_width)
        knb.add(
            *[types.InlineKeyboardButton(text=text[0], url=text[1]) for text in buttons]
        )
        return knb

    async def answer(self, bot: Bot, uid: int, mid: int, command: str) -> bool:

        if command in command_answer:
            return_answer = command_answer[command]
            knb = await self.text_keyboard(return_answer["button"]) \
                if not return_answer["inline"] \
                else await self.inline_keyboard(return_answer["button"])
            if "image" in return_answer:
                await bot.send_photo(uid,
                                     caption=return_answer["answer"],
                                     photo=open(return_answer["image"], "rb"),
                                     parse_mode="Markdown",
                                     reply_markup=knb
                                     )
            else:
                await bot.send_message(
                    uid,
                    return_answer["answer"],
                    reply_markup=knb,
                    parse_mode="Markdown"
                )
            return True

        else:
            return False

