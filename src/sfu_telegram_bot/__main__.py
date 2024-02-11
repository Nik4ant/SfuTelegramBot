import asyncio
import logging
import os
import sys

sys.path.extend(
    [
        os.path.abspath(f"{os.curdir}/src"),
        os.path.abspath(f"{os.curdir}/src/sfu_telegram_bot"),
    ]
)

from bot import telegram

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(telegram.start())
