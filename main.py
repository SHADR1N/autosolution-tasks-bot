# 54.204.116.207:9989:empt74903bgke190140:JPmqjxQfNVckUbpY_country-UnitedStates
import multiprocessing as mp
from ai_bot import start_bot
from tel_session import start_session


if __name__ == "__main__":
    mp.freeze_support()
    main_bot = mp.Process(target=start_bot)
    main_bot.start()

    tg_session = mp.Process(target=start_session)
    tg_session.start()
