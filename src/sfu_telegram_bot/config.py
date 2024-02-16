from os import environ

from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
ADMIN_ID: str = environ["ADMIN_ID"]
