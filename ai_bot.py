import asyncio
import os
import json
import re
from typing import Union

from models import User, AdminList, ChannelList

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import Unauthorized, BadRequest
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from addons_bot.handler_bot import Handler

load_dotenv()

API_TOKEN = os.environ.get("TOKEN_BOT")

handler = Handler()
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class IsAdmin(BoundFilter):
    key = "is_admin"

    async def check(self, message: types.Message):
        if AdminList.select().where(AdminList.uid == message.from_user.id):
            return True
        else:
            return False


class IsNotAdmin(BoundFilter):
    key = "is_admin"

    async def check(self, message: types.Message):
        if AdminList.select().where(AdminList.uid == message.from_user.id):
            return False
        else:
            return True


class IsSubscribed(BoundFilter):
    key = "is_subscribed"

    async def check(self, message: Union[types.Message, int]):
        uid = message.from_user.id if isinstance(message, types.Message) else message
        User.get_status(uid=uid)

        channel = [chat.channel_id for chat in ChannelList.select()]
        for chat in channel:
            try:
                member = await bot.get_chat_member(chat, uid)

                if member.status in ['kicked', 'left']:
                    return True

            except Unauthorized as ex:
                return True

            except BadRequest as ex:
                return True

        return False


class UrlForm(StatesGroup):
    url_choose = State()


class AddChannel(StatesGroup):
    channel_url = State()
    channel_id = State()
    channel_name = State()


class AddAdmin(StatesGroup):
    user = State()


async def send_answer(async_task_read):
    while True:
        if async_task_read.empty():
            await asyncio.sleep(3)
            continue

        answer = async_task_read.get()
        json_answer = json.loads(answer)
        knb = types.InlineKeyboardMarkup(row_width=1)
        knb.add(
            types.InlineKeyboardButton(text="Удалить", callback_data="delete_message")
        )

        for task in json_answer["tasks"]:
            try:
                await bot.send_message(json_answer["uid"], str(task), reply_markup=knb)
            except:
                pass


def start_bot(task_write, async_task_read):
    @dp.message_handler(IsSubscribed(), IsNotAdmin())
    async def access_denied(message: types.Message):
        uid = message.from_user.id

        knb = types.InlineKeyboardMarkup(row_width=1)
        for channel in list(ChannelList.select()):
            knb.add(
                types.InlineKeyboardButton(text=channel.channel_name, url=channel.channel_url)
            )

        knb.add(
            types.InlineKeyboardButton(text="Я подписался ✅", callback_data="check_access")
        )
        return await bot.send_message(uid,
                                      "*Для использования бота вам необходимо подписать на наши каналы:*",
                                      reply_markup=knb, parse_mode="Markdown")

    @dp.callback_query_handler(IsAdmin(), lambda call: str(call.data).startswith("delete_chat_"))
    async def delete_channel(callback: types.CallbackQuery):
        id_chat = str(callback.data).split("_")[-1]

        chat_delete = ChannelList.select().where(ChannelList.id == int(id_chat))
        if chat_delete:
            chat_delete[0].delete_instance()

        return await bot.edit_message_text(chat_id=callback.from_user.id,
                                           message_id=callback.message.message_id,
                                           text="Канал удален.")

    @dp.callback_query_handler(lambda call: call.data == "delete_message")
    async def delete_message(call: types.CallbackQuery):
        try:
            await bot.delete_message(
                chat_id=call.from_user.id,
                message_id=call.message.message_id
            )
        except:
            pass
        return

    @dp.message_handler(IsAdmin(), state=AddAdmin.user)
    async def add_url(callback: types.Message, state: FSMContext):
        uid = callback.from_user.id
        mid = callback.message_id
        data = callback.text

        if data == "Отмена":
            await state.finish()
            return await handler.answer(bot, uid, mid, "/start")

        try:
            int(data)
        except:
            return await callback.answer("Не верно указан ID, попробуйте еще раз:")

        AdminList.get_or_create(uid=int(data))
        await callback.answer("Админ добавлен.")
        await handler.answer(bot, uid, mid, "/start")
        return await state.finish()

    @dp.message_handler(IsAdmin(), state=AddChannel.channel_url)
    async def add_url(callback: types.Message, state: FSMContext):
        uid = callback.from_user.id
        mid = callback.message_id
        data = callback.text

        if data == "Отмена":
            await state.finish()
            return await handler.answer(bot, uid, mid, "/start")

        if not data.startswith("https://t.me/") or data.endswith("/"):
            return await callback.answer("Не верно указана ссылка, попробуйте еще раз:")

        if ChannelList.select().where(ChannelList.channel_url == data):
            return await callback.answer("Канал уже был добавлен.")

        await state.update_data(channel_url=data)

        await callback.answer("Пришлите ID канала:")
        return await AddChannel.next()

    @dp.message_handler(IsAdmin(), state=AddChannel.channel_id)
    async def add_url(callback: types.Message, state: FSMContext):
        uid = callback.from_user.id
        mid = callback.message_id
        data = callback.text

        if data == "Отмена":
            await state.finish()
            return await handler.answer(bot, uid, mid, "/start")

        try:
            int(data)
        except:
            return await callback.answer("Не верный ID канала. Попробуйте еще раз:")

        await state.update_data(channel_id=int(data))

        await callback.answer("Пришлите название кнопки:")
        return await AddChannel.next()

    @dp.message_handler(IsAdmin(), state=AddChannel.channel_name)
    async def add_name(callback: types.Message, state: FSMContext):
        uid = callback.from_user.id
        mid = callback.message_id
        data = callback.text

        if data == "Отмена":
            await state.finish()
            return await handler.answer(bot, uid, mid, "/start")

        state_date = await state.get_data()
        channel_url = state_date.get("channel_url")
        channel_id = state_date.get("channel_id")

        ChannelList(
            channel_url=channel_url,
            channel_name=data,
            channel_id=channel_id
        ).save()

        await callback.answer("Канал добавлен, убедитесь что БОТ есть в администраторах.")
        await handler.answer(bot, uid, mid, "/start")
        return await state.finish()

    @dp.message_handler(IsAdmin(), lambda message: message.text in [
        "Добавить канал",
        "Список каналов",
        "Добавить админа",
        "/admin"])
    async def admin_menu(message: types.Message, state: FSMContext):
        uid = message.from_user.id
        mid = message.message_id
        command = message.text

        if command == "/admin":
            knb = await handler.text_keyboard([["Добавить канал", "Список каналов", "Добавить админа"]])
            return await bot.send_message(uid, "[Admin panel]", reply_markup=knb)

        if command == "Добавить канал":
            knb = await handler.text_keyboard([["Отмена"]])
            await state.set_state(AddChannel.channel_url.state)
            return await bot.send_message(uid, "Пришлите ссылку на канал:\nФормат: https://t.me/username",
                                          reply_markup=knb)

        if command == "Добавить админа":
            await state.set_state(AddAdmin.user.state)
            return await message.answer("Пришлите ID пользователя:\nБот: @myidbot")

        if command == "Список каналов":
            for chat in list(ChannelList.select()):
                try:
                    knb = types.InlineKeyboardMarkup(row_width=1)
                    knb.add(types.InlineKeyboardButton(text="Удалить", callback_data=f"delete_chat_{chat.id}"))
                    await bot.send_message(uid,
                                           f"Имя: {chat.channel_name}\nСсылка: {chat.channel_url}",
                                           reply_markup=knb)
                except:
                    pass
            return

        return

    @dp.callback_query_handler()
    async def check_access(callback: types.CallbackQuery):
        uid = callback.from_user.id
        mid = callback.message.message_id
        data = callback.data

        if data == "check_access" and not await IsSubscribed().check(uid):
            try:
                await bot.delete_message(chat_id=uid, message_id=mid)
            except:
                pass
            return await handler.answer(bot, uid, mid, "/start")
        else:
            return await bot.answer_callback_query(callback.id, "Подпишитесь на каналы по кнопкам выше.", show_alert=True)

    @dp.message_handler(state=UrlForm.url_choose)
    async def message_state(message: types.Message, state: FSMContext):
        uid = message.from_user.id
        mid = message.message_id
        command = message.text

        if command == "Отмена":
            await state.finish()
            return await handler.answer(bot, uid, mid, command)

        try:
            await bot.delete_message(chat_id=uid, message_id=mid)
        except:
            pass

        url_regex = re.compile(r"^https?://uchebnik\.mos\.ru/")
        if not url_regex.match(command):
            return await handler.answer(bot, uid, mid, "bad_answer")

        task_write.send({
            "uid": uid,
            "url": command
        })
        await handler.answer(bot, uid, mid, "wait_answer")
        return await state.finish()

    @dp.message_handler(lambda message: message.text == "Решить тест 📝")
    async def message_test(message: types.Message, state: FSMContext):
        uid = message.from_user.id

        knb = await handler.text_keyboard([["Отмена"]])
        await state.set_state(UrlForm.url_choose.state)
        await bot.send_message(uid, "*Пришлите ссылку на тест:*", reply_markup=knb, parse_mode="Markdown")
        return

    @dp.message_handler()
    async def message_simple(message: types.Message):
        uid = message.from_user.id
        mid = message.message_id
        command = message.text

        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=message.message_id
            )
        except:
            pass

        if await handler.answer(bot, uid, mid, command):
            return

        return await bot.send_message(uid, "Не известная команад.")

    loop = asyncio.get_event_loop()
    loop.create_task(send_answer(async_task_read))
    dp.bind_filter(IsSubscribed)
    dp.bind_filter(IsAdmin)
    dp.bind_filter(IsNotAdmin)
    executor.start_polling(dp, skip_updates=True)
