from typing import Callable
from enum import Enum

from config import SUPPORTED_LANGUAGES
from .callbacks import *

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
_KEYBOARDS: dict[Keyboard, dict[str, InlineKeyboardMarkup]] = {
    Keyboard.MENU: {},
    Keyboard.ADMIN_MENU: {},
    Keyboard.ADMIN_PANEL: {},
    Keyboard.SETTINGS: {},
    Keyboard.LANGUAGE_SELECT: {},
    Keyboard.TIMETABLE: {},
    Keyboard.LOGOFF: {},
}
# endregion


def get(keyboard_type: Keyboard, lang: str) -> InlineKeyboardMarkup | None:
    return _KEYBOARDS.get(keyboard_type, {}).get(lang, None)


# Must be called only once!
def init(_: Callable) -> None:
    for code in SUPPORTED_LANGUAGES:
        lang: str = code.lower()
        # region Keyboard.MENU + Keyboard.ADMIN_MENU
        menu_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(row_width=2)
        admin_menu_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(row_width=2)

        _btn_today = InlineKeyboardButton(
            text=_("Что сегодня?", locale=lang) + emojize(" :student:"), callback_data=CALLBACK_TIMETABLE_TODAY
        )
        admin_menu_keyboard.add(_btn_today)
        menu_keyboard.add(_btn_today)

        _btn_tomorrow = InlineKeyboardButton(
            text=_("Что завтра?", locale=lang) + emojize(" :student:"), callback_data=CALLBACK_TIMETABLE_TOMORROW
        )
        menu_keyboard.add(_btn_tomorrow)
        admin_menu_keyboard.add(_btn_tomorrow)

        _btn_timetable = InlineKeyboardButton(
            text=_("Расписание", locale=lang) + emojize(" :teacher:"), callback_data=CALLBACK_TIMETABLE_GENERAL
        )
        menu_keyboard.add(_btn_timetable)
        admin_menu_keyboard.add(_btn_timetable)

        _btn_pe_qr = InlineKeyboardButton(
            text=_("Отметиться на физру", locale=lang) + emojize(" :person_cartwheeling:"), callback_data=CALLBACK_PE_QR
        )
        menu_keyboard.add(_btn_pe_qr)
        admin_menu_keyboard.add(_btn_pe_qr)

        _btn_settings = InlineKeyboardButton(
            text=_("Настройки/Settings", locale=lang) + emojize(" :gear:"), callback_data=CALLBACK_SETTINGS
        )
        menu_keyboard.add(_btn_settings)
        admin_menu_keyboard.add(_btn_settings)

        admin_menu_keyboard.add(
            InlineKeyboardButton(
                text=_("Админ-панель", locale=lang), callback_data=CALLBACK_ADMIN_PANEL
            )
        )

        _KEYBOARDS[Keyboard.MENU][lang] = menu_keyboard
        _KEYBOARDS[Keyboard.ADMIN_MENU][lang] = admin_menu_keyboard
        # endregion

        # region Keyboard.SETTINGS
        settings_keyboard = InlineKeyboardMarkup(row_width=2)
        settings_keyboard.add(InlineKeyboardButton(
            text=_("Авторизоваться/Перезайти", locale=lang) + emojize(" :rocket:"), callback_data=CALLBACK_AUTH
        ))
        settings_keyboard.add(InlineKeyboardButton(
            text=_("Написать в поддержку", locale=lang) + emojize(" :ambulance:"), callback_data=CALLBACK_SUPPORT
        ))
        settings_keyboard.add(InlineKeyboardButton(
            text=_("Выбрать язык / Choose language", locale=lang), callback_data=CALLBACK_SELECT_LANG
        ))
        settings_keyboard.row(InlineKeyboardButton(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.SETTINGS][lang] = settings_keyboard
        # endregion

        # region Keyboard.LANGUAGE_SELECT
        # Always the same...
        language_select_keyboard = InlineKeyboardMarkup(row_width=2)
        language_select_keyboard.add(InlineKeyboardButton(
            text="RU", callback_data=CALLBACK_SELECT_RU
        ))
        language_select_keyboard.add(InlineKeyboardButton(
            text="EN", callback_data=CALLBACK_SELECT_EN
        ))
        _KEYBOARDS[Keyboard.LANGUAGE_SELECT][lang] = language_select_keyboard
        # endregion

        # region Keyboard.ADMIN_PANEL
        admin_panel_keyboard = InlineKeyboardMarkup(row_width=2)
        admin_panel_keyboard.add(InlineKeyboardButton(
            text=_("Почистить бд", locale=lang), callback_data=CALLBACK_DB_GC
        ))
        admin_panel_keyboard.add(InlineKeyboardButton(
            text=_("Очистить кэш расписаний", locale=lang), callback_data=CALLBACK_CLEAR_TIMETABLE_CACHE
        ))
        admin_panel_keyboard.row(InlineKeyboardButton(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.ADMIN_PANEL][lang] = admin_panel_keyboard
        # endregion

        # region Keyboard.TIMETABLE
        timetable_keyboard = InlineKeyboardMarkup(row_width=2)
        timetable_keyboard.row(InlineKeyboardButton(
            text=_("Эта неделя", locale=lang), callback_data=CALLBACK_THIS_WEEK
        ))
        timetable_keyboard.add(InlineKeyboardButton(
            text=_("Чётная неделя", locale=lang), callback_data=CALLBACK_EVEN_WEEK
        ))
        timetable_keyboard.add(InlineKeyboardButton(
            text=_("Нечётная неделя", locale=lang), callback_data=CALLBACK_ODD_WEEK
        ))
        admin_panel_keyboard.row(InlineKeyboardButton(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.TIMETABLE][lang] = timetable_keyboard
        # endregion

        # region Keyboard.LOGOFF
        logoff_keyboard = InlineKeyboardMarkup()
        logoff_keyboard.row(InlineKeyboardButton(
            text=_("Перезайти", locale=lang), callback_data=CALLBACK_AUTH
        ))
        logoff_keyboard.row(InlineKeyboardButton(
            text=_("В меню", locale=lang), callback_data=CALLBACK_TO_MENU
        ))
        _KEYBOARDS[Keyboard.LOGOFF][lang] = logoff_keyboard
        # endregion
