import logging
import functools
from typing import Callable, Any

import aiogram.utils.exceptions as exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from emoji import emojize

import database as db
from sfu_api import timetable, usport
from sfu_api.timetable import parser as timetable_parser
from bot import support
from bot.app import keyboards
from config import ADMIN_ID, TELEGRAM_TOKEN
from validation import *


bot: Bot = Bot(token=TELEGRAM_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=MemoryStorage())


class UserDataInputState(StatesGroup):
	login = State()
	group = State()
	subgroup = State()


class SupportMessageInput(StatesGroup):
	user_message = State()


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.reply(
			f"Добро пожаловать, {message.from_user.first_name}!",
			reply_markup=keyboards.admin_menu_board,
		)
	else:
		await message.reply(
			"Добро пожаловать, авторизуйтесь для начала работы.",
			reply_markup=keyboards.menu_board,
		)


# region    -- Utils/Other
def update_interaction_time(func: Callable) -> Any:
	"""
	Updates last interaction time in db for detected user_id.
	(Assumes that at least 1 argument is Message or CallbackQuery!)
	If no user_id was detected, does nothing.
	"""

	@functools.wraps(func)
	def inner(*args, **kwargs):
		user_id: str | None = None
		for arg in args:
			if isinstance(arg, types.Message):
				user_id = arg.from_user.id
			elif isinstance(arg, types.CallbackQuery):
				user_id = arg.from_user.id
		
		if user_id is not None:
			db.update_interaction_time_for(user_id)
		return func(*args, **kwargs)
	
	return inner
# endregion -- Utils/Other


# region    -- ADMIN
@dp.message_handler(text=("Админ-панель"))
async def admin_panes(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.answer("Админ-панель", reply_markup=keyboards.admin_panel)


@dp.message_handler(text=("Почистить бд"))
async def clear_db(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		db.remove_old_profiles()
		await message.answer("База данных почищена!")


@dp.message_handler(text=("Очистить кэш расписаний"))
async def clear_timetable_cache(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		timetable.cacher.reset_global_cache()


@dp.message_handler(text=("В меню"))
async def back_to_menu(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.answer("Меню", reply_markup=keyboards.admin_menu_board) 
# endregion -- ADMIN


# region    -- Usport
@dp.message_handler(text=emojize("Отметиться на физру :person_cartwheeling:"))
@update_interaction_time
async def pe_qr(message: types.Message) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(message.from_user.id)

	if student is None:
		await message.answer("Ошибка! Вы не авторизовались")
	else:
		try:
			await bot.send_photo(
				chat_id=message.chat.id, photo=usport.get_pe_qr_url(student.sfu_login)
			)
		except exceptions.WrongFileIdentifier as err:
			await message.answer(
				"Возникла ошибка. Проверьте входные данные или обратитесь в поддержку."
			)
			logging.exception(
				"There is an error in receiving the photo. Maybe the user's fault.",
				exc_info=err,
			)
# endregion -- Usport


# region    -- Timetable
@dp.message_handler(text=emojize("Расписание :teacher:"))
async def timetable_sequence_start(message: types.Message) -> None:
	await message.answer("Выберите неделю.", reply_markup=keyboards.timetable_board)


# TODO: student: db.UserModel | None thingy (get_user_if_authenticated) can be handled by a generator?
@dp.message_handler(text=emojize("Что сегодня? :student:"))
@update_interaction_time
async def timetable_today(message: types.Message) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(message.from_user.id)
	if student is None:
		await message.answer("Ошибка! Вы не авторизовались")
		return

	img_path: str | None = await timetable_parser.parse_today(student.group_name, student.subgroup)
	if img_path is None:
		await message.answer("Что-то пошло не так. Попробуйте позже или напишите в поддержку :()")
	else:
		with open(img_path, mode="rb") as img_file:
			await bot.send_photo(chat_id=message.chat.id, photo=img_file)


@update_interaction_time
async def _timetable_week(message: types.Message, target_week_num: int = timetable_parser.WeekNum.CURRENT) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(message.from_user.id)
	if student is None:
		await message.answer("Ошибка! Вы не авторизовались")
		return

	img_paths: list[str] | None = await timetable_parser.parse_week(student.group_name, student.subgroup, target_week_num)
	if img_paths is None:
		await message.answer("Что-то пошло не так. Попробуйте позже или напишите в поддержку :()")
	else:
		for img_path in img_paths:
			with open(img_path, mode="rb") as img_file:
				await bot.send_photo(chat_id=message.chat.id, photo=img_file)


@dp.message_handler(text="Эта неделя")
async def timetable_this_week(message: types.Message) -> None:
	await _timetable_week(message)


@dp.message_handler(text="Четная неделя")
async def timetable_week_even(message: types.Message) -> None:
	await _timetable_week(message, timetable_parser.WeekNum.EVEN)


@dp.message_handler(text="Нечетная неделя")
async def timetable_week_odd(message: types.Message) -> None:
	await _timetable_week(message, timetable_parser.WeekNum.ODD)
# endregion -- Timetable


# region    -- Settings
@dp.message_handler(text=emojize("Настройки/Settings :gear:"))
async def settings(message: types.Message) -> None:
	await message.answer("Выберите настройки", reply_markup=keyboards.settings_board)


@dp.message_handler(text=emojize("Авторизоваться :rocket:"))
async def auth(message: types.Message) -> None:
	if db.get_user_if_authenticated(message.from_user.id) is None:
		await UserDataInputState.login.set()
		await message.answer(
			"Введите ваш логин для входа на usport.\nПример: NSurname-UG24"
		)
	else:
		await message.answer(
			"Вы уже авторизованы. Если хотите перезайти, нажмите 'Перезайти'.",
			reply_markup=keyboards.logoff_choice_board,
		)


@dp.message_handler(text=("Выбрать язык / Choose language"))
async def choose_language(message: types.Message) -> None:
	await message.answer(
		"Выберите язык/Choose your language",
		reply_markup=keyboards.choose_language_board,
	)


@dp.message_handler(text=("RU"))
async def ru_lang(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.answer(
			"The language has been changed to Russian",
			reply_markup=keyboards.admin_menu_board,
		)
	else:
		await message.answer(
			"The language has been changed to Russian",
			reply_markup=keyboards.menu_board,
		)


@dp.message_handler(text=("EN"))
async def en_lang(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.answer(
			"The language has been changed to English",
			reply_markup=keyboards.admin_menu_board,
		)
	else:
		await message.answer(
			"The language has been changed to English",
			reply_markup=keyboards.menu_board,
		)


@dp.message_handler(text="Перезайти")
async def relogin(message: types.Message) -> None:
	await UserDataInputState.login.set()
	await message.answer(
		"Введите ваш логин для входа на usport.\nПример: NSurname-UG24"
	)


@dp.message_handler(text=emojize("Написать в поддержку :ambulance:"))
async def support_message(message: types.Message) -> None:
	await message.answer(
		"Введите ваше сообщение, если хотите сообщить о баге. Отправка фото недоступна."
	)
	await SupportMessageInput.user_message.set()


@dp.message_handler(text="Назад")
async def go_back(message: types.Message) -> None:
	if is_admin(message.from_user.id):
		await message.answer("Вы в меню.", reply_markup=keyboards.admin_menu_board)
	else:
		await message.answer("Вы в меню.", reply_markup=keyboards.menu_board)
# endregion    -- Settings


@dp.message_handler(state=SupportMessageInput.user_message)
async def user_support_message(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		if message.text:
			data["user_message"] = format_message(message.from_user.id, message.text)
			await support.send_message(data["user_message"])

	await state.finish()
	await message.answer("Ваше обращение принято!")


# region    -- Input profile data
@dp.message_handler(state=UserDataInputState.login)
async def add_login(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		data["login"] = format_sfu_login(message.text)
		if not data["login"]:
			await message.answer("Ошибка! Некоректный логин, попробуйте снова")
			return

		await message.answer("Теперь введите название вашей группы\nПример: ВГ24-01Б")
		await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.group)
async def add_group(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		data["group"] = sanitize_str(message.text)
		if not data["group"]:
			await message.answer(
				"Ошибка! Некоректная группа, попробуйте снова\n(Образец: ВГ23-01Б)"
			)
			return

		await message.answer("Введите номер вашей подгруппы (просто число).")
		await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.subgroup)
async def add_subgroup(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		data["subgroup"] = sanitize_str(message.text)
		if not data["subgroup"].isnumeric():
			await message.answer(
				"Ошибка! Подгруппа должна быть числом, попробуйте снова"
			)
			return

		db.create_or_replace_user(message.from_user.id, data["login"], data["group"], data["subgroup"])
		await message.answer("Вы авторизованы!", reply_markup=keyboards.menu_board)
		await state.finish()
# endregion -- Input profile data


def start() -> None:
	executor.start_polling(dp)


async def close() -> None:
	await bot.close_bot()
