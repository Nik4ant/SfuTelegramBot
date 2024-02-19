from aiogram.types import ReplyKeyboardMarkup
from emoji import emojize

menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
menu_board.row(emojize("Что сегодня? :student:"), emojize("Расписание :teacher:"))
menu_board.row(emojize("Отметиться на физру :person_cartwheeling:"))
menu_board.row(emojize("Авторизоваться :rocket:"))

timetable_board = ReplyKeyboardMarkup(resize_keyboard=True)
timetable_board.row("Эта неделя")
timetable_board.row("Четная неделя", "Нечетная неделя")
timetable_board.row("Назад")

logoff_choice_board = ReplyKeyboardMarkup(resize_keyboard=True)
logoff_choice_board.row("Перезайти")
logoff_choice_board.row("Назад")