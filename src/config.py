from os import environ, path
from os import getcwd

import pytz
from dotenv import load_dotenv

load_dotenv()
I18N_LOCALES_DIR = path.join(getcwd(), "locales")
I18N_DOMAIN = "base"
SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")
TELEGRAM_TOKEN: str = environ["TELEGRAM_TOKEN"]
TELEGRAM_SUPPORT_TOKEN: str = environ["TELEGRAM_SUPPORT_TOKEN"]
ADMIN_ID: int = int(environ["ADMIN_ID"])
