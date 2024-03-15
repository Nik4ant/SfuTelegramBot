import logging
import os
import sys

sys.path.extend(
    [
        os.path.abspath(f"{os.curdir}/src/sfu_telegram_bot"),
    ]
)

from bot import support, telegram
from database import init_db


def main() -> None:
    try:
        init_db()
        print("Choose bot ('main' for main bot, 'support' for support bot)")
        choose = str(input())

        if choose == "main":
            telegram.start()
        elif choose == "support":
            support.start()

    except KeyboardInterrupt:
        logging.info("Process interrupted")
    except Exception as e:
        logging.error("Unknown and unhandled exception occurred", exc_info=e)
    finally:
        # aiogram automatically closes the loop and stops the bot...
        # TODO: close aiohttp session used for parsing or just YOLO it?
        logging.info("Successfully shutdown the bot")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
