import argparse
import asyncio
import logging
import os
import sys

from bot import support, telegram
from database import init_db
from sfu_api import timetable


def init_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SfuTelegramBot")
    parser.add_argument(
        "--support_enabled", action="store_true", help="Runs bot in the support mode", default=False
    )
    return parser


def main() -> None:
    # Couldn't find a better way to access args in the "finally" block...
    parser = init_args_parser()
    args = parser.parse_args()

    try:
        if args.support_enabled:
            # Note: Support bot doesn't have database, or anything like that...
            logging.info("Starting the support bot")
            support.start()
        else:
            logging.info("Starting the default bot")
            init_db()
            timetable.img_generator.init()
            timetable.cacher.init_cache_scheduler()
            telegram.start()
    except KeyboardInterrupt:
        logging.info("Process interrupted")
    except Exception as e:
        logging.error("Unknown and unhandled exception occurred", exc_info=e)
    finally:
        asyncio.run(timetable.parser.close_http_session())
        if args.support_enabled:
            asyncio.run(support.close())
        else:
            asyncio.run(telegram.close())
        logging.info("Successfully shutdown the bot")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
