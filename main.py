import multiprocessing as mp
import asyncio
import threading

from dotenv import load_dotenv

from ai_bot import start_bot
from tel_session import start_session

load_dotenv()


if __name__ == "__main__":
    mp.freeze_support()
    task_read, task_write = mp.Pipe(duplex=True)
    async_task_read = mp.Queue()

    main_bot = mp.Process(target=start_bot, kwargs=dict(task_write=task_write, async_task_read=async_task_read))
    tg_session = mp.Process(target=start_session, kwargs=dict(task_read=task_read, async_task_read=async_task_read))

    tg_session.start()
    main_bot.start()
