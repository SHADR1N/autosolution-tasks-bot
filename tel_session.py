import asyncio
import json
import os
import random
import threading
import time

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest

from dotenv import load_dotenv

load_dotenv()
proxy = os.getenv("PROXY")
proxy_type = os.getenv("PROXY_TYPE")
URL_BOT = os.getenv("URL_BOT")

session_obj = []
proxy = {
    "proxy_type": proxy_type,
    "addr": proxy.split(":")[0],
    "port": int(proxy.split(":")[1]),
    "username": proxy.split(":")[2],
    "password": proxy.split(":")[3],
    "rdns": True
}


class QeuenTask:
    def __init__(self, task_read, async_task_read):
        self.task_read = task_read
        self.async_task_read = async_task_read

    async def new_task(self, info: dict, account_data: dict):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        url = info["url"]
        uid = info["uid"]

        with open(account_data[1], "r", encoding="utf-8") as f:
            data = json.load(f)

        account = TelegramClient(
            account_data[0],
            api_id=int(data["app_id"]),
            api_hash=data["app_hash"],
            proxy=proxy,
            auto_reconnect=True,
            request_retries=2,
            connection_retries=2,
            loop=loop
        )
        try:
            await account.connect()
        except Exception as ex:
            result = {
                "uid": uid,
                "tasks": ["Не смог найти ответы, попробуйте еще раз."]
            }
            self.async_task_read.put(str(json.dumps(result)))
            session_obj.append(account_data)
            return

        if await account.is_user_authorized():
            await account.start()
        else:
            result = {
                "uid": uid,
                "tasks": ["Не смог найти ответы, попробуйте еще раз."]
            }
            self.async_task_read.put(str(json.dumps(result)))
            session_obj.append(account_data)
            return
        try:
            chat_send = await self.get_access_to_bot(account)

            await account.send_message(chat_send, url)
            await asyncio.sleep(15)
            message_answer = await account.get_messages(chat_send, limit=20)
        except:
            result = {
                "uid": uid,
                "tasks": ["Не смог найти ответы, попробуйте еще раз."]
            }
            self.async_task_read.put(str(json.dumps(result)))
            session_obj.append(account_data)
            return

        answer = []
        for message in message_answer:
            text = message.message
            if text == url:
                break
            if "ЗАДАНИЕ:" in text:
                answer.append(text)

        if not answer:
            answer.append("Для продолжения вам необходима подписка.")

        result = {
            "uid": uid,
            "tasks": answer
        }
        self.async_task_read.put(str(json.dumps(result)))
        session_obj.append(account_data)
        await self.disconnect(account)
        loop.close()
        return

    async def get_access_to_bot(self, account):
        chat_send = await account.get_entity(URL_BOT)
        while True:
            await account.send_message(chat_send, "/start")
            await asyncio.sleep(5)

            res = await account.get_messages(chat_send, limit=1)
            last_message = res[-1].message

            if "@" in last_message:
                url_chat = [i for i in last_message.split(" ") if "@" in i][0]

                await account(JoinChannelRequest(url_chat))
                await asyncio.sleep(2)

            elif last_message == "В каком вы классе?":
                await res[-1].click(5)
                await asyncio.sleep(2)

            elif last_message == "Отправьте ссылку на тест":
                break

        return chat_send

    @staticmethod
    async def disconnect(account):
        try:
            await account.disconnect()
        except:
            return

    def run(self):
        while True:
            info = self.task_read.recv()

            use_task = False
            while not use_task:
                if session_obj:
                    account = session_obj[0]
                    del session_obj[0]
                    threading.Thread(target=asyncio.run, args=(self.new_task(info, account),)).start()
                    use_task = True

                if not use_task:
                    time.sleep(10)


def start_session(task_read, async_task_read):
    json_files = []
    for file in os.listdir("sessions"):
        if file.endswith(".json"):
            json_files.append(file)

    for js in json_files:
        js_path = os.path.join("sessions", js)
        with open(js_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        session_file = data["session_file"]
        session_file = os.path.join("sessions", session_file + ".session")

        if os.path.exists(session_file):
            session_obj.append([session_file, js_path])

    random.shuffle(session_obj)
    task = QeuenTask(task_read, async_task_read)
    task.run()
