import logging
import os
import sys

sys.path.extend(
    [
        os.path.abspath(f"{os.curdir}/src"),  # might be unnecessary
        os.path.abspath(f"{os.curdir}/src/sfu_telegram_bot"),
    ]
)

from bot import telegram
from database import init_db


def main() -> None:
    init_db()
    telegram.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
