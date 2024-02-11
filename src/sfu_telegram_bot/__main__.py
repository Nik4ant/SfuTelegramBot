import logging
import os
import sys

sys.path.extend(
    [
        os.path.abspath(f"{os.curdir}/src"),  # might be unnecessary
        os.path.abspath(f"{os.curdir}/src/sfu_telegram_bot"),
        os.path.abspath(f"{os.curdir}/src/sfu_telegram_bot/bot"),
    ]
)

from bot import telegram


def main() -> None:
    telegram.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
