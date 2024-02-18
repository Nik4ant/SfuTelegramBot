from os import environ

from dotenv import load_dotenv
import pytz


load_dotenv()
SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")
TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
ADMIN_ID: str = environ["ADMIN_ID"]
