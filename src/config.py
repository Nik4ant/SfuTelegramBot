from os import environ, path
from os import getcwd

import pytz
from dotenv import load_dotenv

load_dotenv()

I18N_LOCALES_DIR = path.join(getcwd(), "locales")
I18N_DOMAIN = "sfu_telegram_bot"
SUPPORTED_LANGUAGES: list[str] = ["EN", "RU"]

SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")

TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
TELEGRAM_SUPPORT_TOKEN: str = environ["TELEGRAM_SUPPORT_TOKEN"]
ADMIN_IDS: list[int] = []
if environ.get("ADMIN_IDS", False):
    # Format: [ID1],[ID2],[ID3]
    ADMIN_IDS.extend(map(int, environ["ADMIN_IDS"].split(',')))
