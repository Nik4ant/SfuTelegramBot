from os import environ

import pytz
from dotenv import load_dotenv

load_dotenv()
SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")
TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
TELEGRAM_SUPPORT_TOKEN: str = environ["TELEGRAM_SUPPORT_TOKEN"]
ADMIN_ID: int = int(environ["ADMIN_ID"])
