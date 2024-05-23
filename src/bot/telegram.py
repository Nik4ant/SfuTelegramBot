import logging
import functools
from typing import Callable, Any

import aiogram.utils.exceptions as exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from emoji import emojize

import database as db
from sfu_api import timetable, usport
from sfu_api.timetable import parser as timetable_parser
from bot import support
from bot.app import keyboards
from bot.app.keyboards import Keyboard
from bot.app.callbacks import *
from config import TELEGRAM_TOKEN, I18N_DOMAIN, I18N_LOCALES_DIR
from validation import *


bot: Bot = Bot(token=TELEGRAM_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=MemoryStorage())

i18n = I18nMiddleware(I18N_DOMAIN, I18N_LOCALES_DIR)
dp.setup_middleware(i18n)
_ = i18n.gettext  # alias for translating text


class UserDataInputState(StatesGroup):
	login = State()
	group = State()
	subgroup = State()


class SupportMessageInput(StatesGroup):
	user_message = State()


# TODO: telegram state, db + default "ru"
def get_lang_for(user_id: int, fetch_db_if_not_found: bool = True) -> str:
	"""
	Returns language based on telegram state or db or default values
	@param user_id: Telegram id
	@param fetch_db_if_not_found: If False only searches in telegram state
	@return: Language code
	"""
	# TODO: add telegram state/cache to avoid hitting db every time...
	lang: str | None = db.get_lang_for(user_id)
	if lang is None:
		return "en"
	return lang


@dp.message_handler(commands=["start"])
async def welcome_menu(message: types.Message) -> None:
	_lang: str = get_lang_for(message.from_user.id)

	if is_admin(message.from_user.id):
		await message.reply(
			_("Добро пожаловать", locale=_lang) + ", " + message.from_user.first_name + '!',
			reply_markup=keyboards.get(Keyboard.ADMIN_PANEL, _lang),
		)
	else:
		await message.reply(
			_("Добро пожаловать, авторизуйтесь для начала работы", locale=_lang),
			reply_markup=keyboards.get(Keyboard.MENU, _lang),
		)


# region    -- Utils/Other
def _is(target: Any) -> Callable:
	return lambda callback: callback.data == target


def update_interaction_time(func: Callable) -> Any:
	"""
	Updates last interaction time in db for detected user_id.
	(Assumes that at least 1 argument is Message or types.CallbackQuery!)
	If no user_id was detected, does nothing.
	"""

	@functools.wraps(func)
	def inner(*args, **kwargs):
		user_id: int | None = None
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
@dp.callback_query_handler(_is(CALLBACK_ADMIN_PANEL))
async def admin_panel(query: types.CallbackQuery) -> None:
	if is_admin(query.from_user.id):
		_lang: str = get_lang_for(query.from_user.id)
		await query.message.answer(
			_("Админ-панель", locale=_lang), reply_markup=keyboards.get(Keyboard.ADMIN_PANEL, _lang)
		)


@dp.callback_query_handler(_is(CALLBACK_DB_GC))
async def clear_db(query: types.CallbackQuery) -> None:
	if is_admin(query.from_user.id):
		db.remove_old_profiles()
		await query.message.answer(_("База данных почищена", locale=get_lang_for(query.from_user.id)) + '!')


@dp.callback_query_handler(_is(CALLBACK_CLEAR_TIMETABLE_CACHE))
async def clear_timetable_cache(query: types.CallbackQuery) -> None:
	if is_admin(query.from_user.id):
		timetable.cacher.reset_global_cache()
		await query.message.answer(_("Кэш изображений удалён", locale=get_lang_for(query.from_user.id)) + '!')
# endregion -- ADMIN


# region    -- COMMON
@dp.callback_query_handler(_is(CALLBACK_TO_MENU))
async def back_to_menu(query: types.CallbackQuery) -> None:
	_lang: str = get_lang_for(query.message.from_user.id)

	if is_admin(query.message.from_user.id):
		await query.message.reply(
			_("Меню", locale=_lang), reply_markup=keyboards.get(Keyboard.ADMIN_PANEL, _lang),
		)
	else:
		await query.message.reply(
			_("Меню", locale=_lang), reply_markup=keyboards.get(Keyboard.MENU, _lang),
		)
# endregion -- COMMON


# region    -- Usport
@dp.callback_query_handler(_is(CALLBACK_PE_QR))
@update_interaction_time
async def pe_qr(query: types.CallbackQuery) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(query.message.from_user.id)

	if student is None:
		await query.message.answer(
			_("Ошибка! Вы не авторизовались", locale=get_lang_for(query.from_user.id, False))
		)
	else:
		try:
			await bot.send_photo(
				chat_id=query.message.chat.id, photo=usport.get_pe_qr_url(student.sfu_login)
			)
		except exceptions.WrongFileIdentifier as err:
			await query.message.answer(
				_("Возникла ошибка. Проверьте входные данные или обратитесь в поддержку", locale=student.lang)
			)
			logging.exception(
				"There is an error in receiving the photo. Maybe it's user's fault.",
				exc_info=err,
			)
# endregion -- Usport


# region    -- Timetable
@dp.callback_query_handler(_is(CALLBACK_TIMETABLE_GENERAL))
async def timetable_sequence_start(query: types.CallbackQuery) -> None:
	_lang: str = get_lang_for(query.from_user.id)
	await query.answer()
	await query.message.answer(
		_("Выберите неделю", locale=_lang), reply_markup=keyboards.get(Keyboard.TIMETABLE, _lang)
	)


@dp.callback_query_handler(_is(CALLBACK_TIMETABLE_TODAY))
@update_interaction_time
async def timetable_today(query: types.CallbackQuery) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(query.from_user.id)
	if student is None:
		await query.message.answer(
			_("Ошибка! Вы не авторизовались", locale=get_lang_for(query.from_user.id, False))
		)
		return

	img_path: str | None = await timetable_parser.parse_today(student.group_name, student.subgroup)
	if img_path is None:
		await query.message.answer(
			_("Что-то пошло не так. Попробуйте позже или напишите в поддержку", locale=student.lang) + ":()"
		)
	else:
		with open(img_path, mode="rb") as img_file:
			await bot.send_photo(chat_id=query.message.chat.id, photo=img_file)


@update_interaction_time
async def _timetable_week(message: types.Message, target_week_num: int = timetable_parser.WeekNum.CURRENT) -> None:
	student: db.UserModel | None = db.get_user_if_authenticated(message.from_user.id)
	if student is None:
		await message.answer(_("Ошибка! Вы не авторизовались"))
		return

	img_path: str | None = await timetable_parser.parse_week(student.group_name, student.subgroup, target_week_num)
	if img_path is None:
		await message.answer(_("Что-то пошло не так. Попробуйте позже или напишите в поддержку") + ":()")
	else:
		with open(img_path, mode="rb") as img_file:
			await bot.send_photo(chat_id=message.chat.id, photo=img_file)


@dp.callback_query_handler(_is(CALLBACK_THIS_WEEK))
async def timetable_this_week(query: types.CallbackQuery) -> None:
	await _timetable_week(query.message)


@dp.callback_query_handler(_is(CALLBACK_EVEN_WEEK))
async def timetable_week_even(query: types.CallbackQuery) -> None:
	await _timetable_week(query.message, timetable_parser.WeekNum.EVEN)


@dp.callback_query_handler(_is(CALLBACK_ODD_WEEK))
async def timetable_week_odd(query: types.CallbackQuery) -> None:
	await _timetable_week(query.message, timetable_parser.WeekNum.ODD)
# endregion -- Timetable


# region    -- Settings
@dp.callback_query_handler(lambda call: call.data == CALLBACK_SETTINGS)
async def settings(query: types.CallbackQuery) -> None:
	_lang: str = get_lang_for(query.from_user.id)
	await query.message.answer(
		_("Выберите настройки", locale=_lang), reply_markup=keyboards.get(Keyboard.SETTINGS, _lang)
	)


@dp.callback_query_handler(_is(CALLBACK_SELECT_LANG))
async def choose_language(query: types.CallbackQuery) -> None:
	_lang: str = get_lang_for(query.from_user.id)
	await query.message.answer(
		_("Выберите язык/Choose your language", locale=_lang),
		reply_markup=keyboards.get(Keyboard.LANGUAGE_SELECT, _lang),
	)


# TODO: actually change language in the database -_-
@dp.callback_query_handler(_is(CALLBACK_SELECT_RU))
async def ru_lang(query: types.CallbackQuery) -> None:
	i18n.reload()

	if is_admin(query.from_user.id):
		await query.message.answer(
			"Язык был сменён на русский",
			reply_markup=keyboards.get(Keyboard.ADMIN_PANEL, "RU"),
		)
	else:
		await query.message.answer(
			"Язык был сменён на русский",
			reply_markup=keyboards.get(Keyboard.MENU, "RU"),
		)


@dp.callback_query_handler(_is(CALLBACK_SELECT_EN))
async def en_lang(query: types.CallbackQuery) -> None:
	i18n.reload()

	if is_admin(query.from_user.id):
		await query.message.answer(
			"Language has been changed to English",
			reply_markup=keyboards.get(Keyboard.ADMIN_PANEL, "EN"),
		)
	else:
		await query.message.answer(
			"Language has been changed to English",
			reply_markup=keyboards.get(Keyboard.MENU, "EN"),
		)


@dp.callback_query_handler(_is(CALLBACK_SUPPORT))
async def support_message(query: types.CallbackQuery) -> None:
	await query.message.answer(
		_("Введите ваше сообщение (отправка фото недоступна)", locale=get_lang_for(query.from_user.id))
	)
	await SupportMessageInput.user_message.set()
# endregion    -- Settings


@dp.message_handler(state=SupportMessageInput.user_message)
async def user_support_message(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		if message.text:
			data["user_message"] = format_support_message(message.from_user.id, message.text)
			await support.send_message(data["user_message"])

	await state.finish()
	await message.answer(_("Ваше обращение принято") + '!')


# region    -- Input profile data
@dp.callback_query_handler(_is(CALLBACK_AUTH))
async def auth(query: types.CallbackQuery) -> None:
	_lang: str = get_lang_for(query.from_user.id)

	if db.get_user_if_authenticated(query.from_user.id) is None:
		await UserDataInputState.login.set()
		await query.message.answer(
			_("Введите ваш логин СФУ.\nПример: NSurname-UG24", locale=_lang)
		)
	else:
		await query.message.answer(
			_("Вы уже авторизованы. Если хотите перезайти, нажмите 'Перезайти'", locale=_lang),
			reply_markup=keyboards.get(Keyboard.LOGOFF, _lang),
		)


@dp.message_handler(state=UserDataInputState.login)
async def add_login(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		_lang: str = get_lang_for(message.from_user.id)
		data["lang"] = _lang
		data["login"] = format_sfu_login(message.text)

		if not data["login"]:
			await message.answer(_("Ошибка! Некоректный логин, попробуйте снова", locale=_lang))
			return

		await message.answer(_("Теперь введите название вашей группы\nПример: ВГ24-01Б", locale=_lang))
		await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.group)
async def add_group(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		_lang: str = data["lang"]
		data["group"] = sanitize_str(message.text)

		if not data["group"]:
			await message.answer(
				_("Ошибка! Некоректная группа, попробуйте снова\n(Образец: ВГ23-01Б)", locale=_lang)
			)
			return

		await message.answer(_("Введите номер вашей подгруппы (просто число)", locale=_lang))
		await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.subgroup)
async def add_subgroup(message: types.Message, state: FSMContext) -> None:
	async with state.proxy() as data:
		data["subgroup"] = sanitize_str(message.text)
		_lang: str = data["lang"]

		if not data["subgroup"].isnumeric():
			await message.answer(
				_("Ошибка! Подгруппа должна быть числом, попробуйте снова", locale=_lang)
			)
			return

		db.create_or_replace_user(message.from_user.id, data["login"], data["group"], data["subgroup"], _lang)
		await message.answer(
			_("Вы авторизованы!", locale=_lang), reply_markup=keyboards.get(Keyboard.MENU, _lang)
		)
		await state.finish()
# endregion -- Input profile data


def start() -> None:
	keyboards.init(_)
	executor.start_polling(dp)


async def close() -> None:
	await bot.close_bot()
