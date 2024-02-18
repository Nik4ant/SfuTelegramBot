import bleach


def format_sfu_login(login: str) -> str:
    return ''.join([
        char for char in sanitize_str(login)
        if char.isalnum() or char in "-"
    ])


def sanitize_str(value: str) -> str:
    return bleach.clean(value, strip=True)
