from typing import Callable, Any
from enum import Enum

from config import SUPPORTED_LANGUAGES
from .callbacks import *

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from emoji import emojize


# region Keyboards
class Keyboard(Enum):
    MENU = 1
    ADMIN_MENU = 2
    ADMIN_PANEL = 4
    SETTINGS = 8
    LANGUAGE_SELECT = 16
    TIMETABLE = 32
    LOGOFF = 64


# Contains translated variants of all available keyboards
# (see init below)
_KEYBOARDS: dict[Keyboard, dict[str, ReplyKeyboardMarkup]] = {
    Keyboard.MENU: {},
    Keyboard.ADMIN_MENU: {},
    Keyboard.ADMIN_PANEL: {},
    Keyboard.SETTINGS: {},
    Keyboard.LANGUAGE_SELECT: {},
    Keyboard.TIMETABLE: {},
    Keyboard.LOGOFF: {},
}

# NOTE: ReplyKeyboardMarkup doesn't support callback_data, so the only way to get around that
# is to map each callback to a corresponding translated strings, silly, but better than nothing
_DP_DATA: dict[Any, list[str]] = {}


def __map_callback_to_text(text: str, callback_data) -> KeyboardButton:
    if callback_data not in _DP_DATA:
        _DP_DATA[callback_data] = [text]
    elif text not in _DP_DATA[callback_data]:
        _DP_DATA[callback_data].append(text)

    return KeyboardButton(text=text)


def get_dp_text_variants(callback: Any) -> list[str]:
    return _DP_DATA.get(callback, [])
# endregion


def get(keyboard_type: Keyboard, lang: str) -> ReplyKeyboardMarkup | None:
    return _KEYBOARDS.get(keyboard_type, {}).get(lang, None)


def is_ready() -> bool:
    return len(_DP_DATA) != 0


def init(_: Callable) -> None:
    for code in SUPPORTED_LANGUAGES:
        lang: str = code.lower()
        # region Keyboard.MENU + Keyboard.ADMIN_MENU
        menu_keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(resize_keyboard=True)
        admin_menu_keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(resize_keyboard=True)
        
        _btn_today = __map_callback_to_text(
            text=_("Что сегодня?", locale=lang) + emojize(" :student:"), callback_data=CALLBACK_TIMETABLE_TODAY
        )
        _btn_tomorrow = __map_callback_to_text(
            text=_("Что завтра?", locale=lang) + emojize(" :student:"), callback_data=CALLBACK_TIMETABLE_TOMORROW
        )

        admin_menu_keyboard.row(_btn_today, _btn_tomorrow)
        menu_keyboard.row(_btn_today, _btn_tomorrow)

        _btn_timetable = __map_callback_to_text(
            text=_("Расписание", locale=lang) + emojize(" :teacher:"), callback_data=CALLBACK_TIMETABLE_GENERAL
        )
        menu_keyboard.row(_btn_timetable)
        admin_menu_keyboard.row(_btn_timetable)

        _btn_pe_qr = __map_callback_to_text(
            text=_("Отметиться на физру", locale=lang) + emojize(" :person_cartwheeling:"), callback_data=CALLBACK_PE_QR
        )
        menu_keyboard.row(_btn_pe_qr)
        admin_menu_keyboard.row(_btn_pe_qr)

        _btn_settings = __map_callback_to_text(
            text=_("Настройки/Settings", locale=lang) + emojize(" :gear:"), callback_data=CALLBACK_SETTINGS
        )
        menu_keyboard.row(_btn_settings)
        admin_menu_keyboard.row(
            _btn_settings,
            __map_callback_to_text(
                text=_("Админ-панель", locale=lang), callback_data=CALLBACK_ADMIN_PANEL
            )
        )

        _KEYBOARDS[Keyboard.MENU][lang] = menu_keyboard
        _KEYBOARDS[Keyboard.ADMIN_MENU][lang] = admin_menu_keyboard
        # endregion

        # region Keyboard.SETTINGS
        settings_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        settings_keyboard.row(__map_callback_to_text(
            text=_("Авторизоваться/Перезайти", locale=lang) + emojize(" :rocket:"), callback_data=CALLBACK_AUTH
        ))
        settings_keyboard.row(
            __map_callback_to_text(
                text=_("Написать в поддержку", locale=lang) + emojize(" :ambulance:"), callback_data=CALLBACK_SUPPORT
            ),
            __map_callback_to_text(
                text=_("Выбрать язык / Choose language", locale=lang), callback_data=CALLBACK_SELECT_LANG
            )
        )
        settings_keyboard.row(__map_callback_to_text(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.SETTINGS][lang] = settings_keyboard
        # endregion

        # region Keyboard.LANGUAGE_SELECT
        # Always the same...
        language_select_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        language_select_keyboard.add(__map_callback_to_text(
            text="RU", callback_data=CALLBACK_SELECT_RU
        ))
        language_select_keyboard.add(__map_callback_to_text(
            text="EN", callback_data=CALLBACK_SELECT_EN
        ))
        _KEYBOARDS[Keyboard.LANGUAGE_SELECT][lang] = language_select_keyboard
        # endregion

        # region Keyboard.ADMIN_PANEL
        admin_panel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        admin_panel_keyboard.add(__map_callback_to_text(
            text=_("Почистить бд", locale=lang), callback_data=CALLBACK_DB_GC
        ))
        admin_panel_keyboard.add(__map_callback_to_text(
            text=_("Очистить кэш расписаний", locale=lang), callback_data=CALLBACK_CLEAR_TIMETABLE_CACHE
        ))
        admin_panel_keyboard.row(__map_callback_to_text(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.ADMIN_PANEL][lang] = admin_panel_keyboard
        # endregion

        # region Keyboard.TIMETABLE
        timetable_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        timetable_keyboard.row(__map_callback_to_text(
            text=_("Эта неделя", locale=lang), callback_data=CALLBACK_THIS_WEEK
        ))
        timetable_keyboard.row(
            __map_callback_to_text(
                text=_("Чётная неделя", locale=lang), callback_data=CALLBACK_EVEN_WEEK
            ),
            __map_callback_to_text(
                text=_("Нечётная неделя", locale=lang), callback_data=CALLBACK_ODD_WEEK
            )
        )
        timetable_keyboard.row(__map_callback_to_text(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.TIMETABLE][lang] = timetable_keyboard
        # endregion

        # region Keyboard.LOGOFF
        logoff_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        logoff_keyboard.row(__map_callback_to_text(
            text=_("Перезайти", locale=lang), callback_data=CALLBACK_AUTH
        ))
        logoff_keyboard.row(__map_callback_to_text(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.LOGOFF][lang] = logoff_keyboard
        # endregion
