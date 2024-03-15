from aiogram.types import ReplyKeyboardMarkup
from emoji import emojize

menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
menu_board.row(emojize("Что сегодня? :student:"), emojize("Расписание :teacher:"))
menu_board.row(emojize("Отметиться на физру :person_cartwheeling:"))
menu_board.row(emojize("Настройки/Settings :gear:"))

admin_menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu_board.row(emojize("Что сегодня? :student:"), emojize("Расписание :teacher:"))
admin_menu_board.row(emojize("Отметиться на физру :person_cartwheeling:"))
admin_menu_board.row(emojize("Настройки/Settings :gear:"))
admin_menu_board.row("Админ-панель")

settings_board = ReplyKeyboardMarkup(resize_keyboard=True)
settings_board.row("Выбрать язык / Choose language")
settings_board.row(
    emojize("Авторизоваться :rocket:"), emojize("Написать в поддержку :ambulance:")
)
settings_board.row("Назад")

choose_language_board = ReplyKeyboardMarkup(resize_keyboard=True)
choose_language_board.row("RU", "EN")

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.row("Почистить бд", "Очистить кэш расписаний")
admin_panel.row("В меню")

timetable_board = ReplyKeyboardMarkup(resize_keyboard=True)
timetable_board.row("Эта неделя")
timetable_board.row("Четная неделя", "Нечетная неделя")
timetable_board.row("Назад")

logoff_choice_board = ReplyKeyboardMarkup(resize_keyboard=True)
logoff_choice_board.row("Перезайти")
logoff_choice_board.row("Назад")
