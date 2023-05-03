import multiprocessing as mp
import os
from dotenv import load_dotenv

from ai_bot import start_bot
from tel_session import start_session

load_dotenv()

proxy = os.environ.get("PROXY")
TOKEN_BOT = os.environ.get("TOKEN_BOT")


if __name__ == "__main__":
    mp.freeze_support()
    main_bot = mp.Process(target=start_bot, args=(TOKEN_BOT,))
    main_bot.start()

    tg_session = mp.Process(target=start_session)
    tg_session.start()
