import bleach
from config import ADMIN_ID


def is_admin(telegram_id: int) -> bool:
    return ADMIN_ID == telegram_id


def format_sfu_login(login: str) -> str:
    return "".join(
        [char for char in sanitize_str(login) if char.isalnum() or char in "-"]
    )


def sanitize_str(value: str) -> str:
    return bleach.clean(value, strip=True)


def format_message(user_id: int, message: str):
    return str("USER ID: " + str(user_id) + " MESSAGE: " + message)
