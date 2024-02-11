from os import environ

from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
