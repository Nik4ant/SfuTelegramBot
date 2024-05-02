from aiogram.types import ReplyKeyboardMarkup
from emoji import emojize


menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
settings_board = ReplyKeyboardMarkup(resize_keyboard=True)
choose_language_board = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
timetable_board = ReplyKeyboardMarkup(resize_keyboard=True)
logoff_choice_board = ReplyKeyboardMarkup(resize_keyboard=True)


def reload(_, lang: str = "ru") -> None:
    """
    Reloads all keyboards based on given translate (gettext) function
    @param _: Alias for gettext
    """
    # NOTE: YES! It's bad to change a ton of global objects, but that the whole point - reset every keyboard
    # TODO: test if this global really necessary (try without it and see if it works)
    global menu_board, admin_menu_board, settings_board, \
        choose_language_board, admin_panel, timetable_board, logoff_choice_board

    menu_board.clean()
    menu_board.row(_("Что сегодня?", locale=lang) + emojize(" :student:"), _("Расписание", locale=lang) + emojize(" :teacher:"))
    menu_board.row(_("Отметиться на физру", locale=lang) + emojize(" :person_cartwheeling:"))
    menu_board.row(_("Настройки/Settings", locale=lang) + emojize(" :gear:"))

    admin_menu_board.clean()
    admin_menu_board.row(_("Что сегодня?", locale=lang) + emojize(" :student:"), _("Расписание", locale=lang) + emojize(" :teacher:"))
    admin_menu_board.row(_("Отметиться на физру", locale=lang) + emojize(" :person_cartwheeling:"))
    admin_menu_board.row(_("Настройки/Settings", locale=lang) + emojize(" :gear:"))
    admin_menu_board.row(_("Админ-панель", locale=lang))

    settings_board.clean()
    settings_board.row(
        _("Авторизоваться", locale=lang) + emojize(" :rocket:"), _("Написать в поддержку", locale=lang) + emojize(" :ambulance:")
    )
    settings_board.row(_("Выбрать язык / Choose language", locale=lang))
    settings_board.row(_("Назад", locale=lang))

    choose_language_board.clean()
    choose_language_board.row("RU", "EN")

    admin_panel.clean()
    admin_panel.row(_("Почистить бд", locale=lang), _("Очистить кэш расписаний", locale=lang))
    admin_panel.row(_("В меню", locale=lang))

    timetable_board.clean()
    timetable_board.row(_("Эта неделя", locale=lang))
    timetable_board.row(_("Четная неделя", locale=lang), _("Нечетная неделя", locale=lang))
    timetable_board.row(_("Назад", locale=lang))

    logoff_choice_board.clean()
    logoff_choice_board.row(_("Перезайти", locale=lang))
    logoff_choice_board.row(_("Назад", locale=lang))
