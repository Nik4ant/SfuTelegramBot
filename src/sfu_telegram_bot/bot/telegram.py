import logging
from parser import timetable, usport

import aiogram.utils.exceptions as exceptions
import database as db
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.app import keyboards
from config import ADMIN_ID, TELEGRAM_TOKEN
from emoji import emojize
from validation import *

bot: Bot = Bot(token=TELEGRAM_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=MemoryStorage())


class UserDataInputState(StatesGroup):
    login = State()
    group = State()
    subgroup = State()


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        await message.reply(
            f"Добро пожаловать, {message.from_user.first_name}!",
            reply_markup=keyboards.admin_menu_board,
        )
    else:
        await message.reply(
            "Добро пожаловать, авторизуйтесь для начала работы.",
            reply_markup=keyboards.menu_board,
        )


@dp.message_handler(text=("Админ-панель"))
async def clear_db(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        await message.answer("Админ-панель", reply_markup=keyboards.admin_panel)


@dp.message_handler(text=("Почистить бд"))
async def clear_db(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        db.remove_old_profiles()
        await message.answer("База данных почищена!")


# TODO: add support
@dp.message_handler(text=("Почитать сообщения"))
async def clear_db(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        await message.answer("у вас ?? сообщений. Введите число сообщения.")


# TODO: add a function for cleaning cache (and add cache)
@dp.message_handler(text=("Очистить кэш расписаний"))
async def clear_db(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        await message.answer("Кэш расписаний очищен!")


@dp.message_handler(text=("В меню"))
async def clear_db(message: types.Message) -> None:
    if message.from_user.id == int(ADMIN_ID):
        await message.answer("Меню", reply_markup=keyboards.admin_menu_board)


# region    -- Usport
@dp.message_handler(text=emojize("Отметиться на физру :person_cartwheeling:"))
async def pe_qr(message: types.Message) -> None:
    student: db.UserModel | None = db.get_user_by_id(message.from_user.id)

    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        try:
            await bot.send_photo(
                chat_id=message.chat.id, photo=usport.get_pe_qr_url(student.sfu_login)
            )
        except exceptions.WrongFileIdentifier as err:
            # just imagine that we have a support bot :)
            await message.answer(
                "Возникла ошибка. Проверьте входные данные или обратитесь в поддержку."
            )
            logging.exception(
                "There is an error in receiving the photo. Maybe the user's fault.",
                exc_info=err,
            )


# endregion -- Usport


# region    -- Timetable
# TODO: Code feels the same; Add decorator for timetable endpoints?
@dp.message_handler(text=emojize("Что сегодня? :student:"))
async def timetable_today(message: types.Message) -> None:
    student: db.UserModel | None = db.get_user_by_id(message.from_user.id)
    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        result: list[timetable.Lesson] = await timetable.parse_today(
            student.group_name, student.subgroup
        )
        await message.answer(timetable.format_day(result))


@dp.message_handler(text=emojize("Расписание :teacher:"))
async def timetable_sequence_start(message: types.Message) -> None:
    await message.answer("Выберите неделю.", reply_markup=keyboards.timetable_board)


@dp.message_handler(text="Эта неделя")
async def timetable_this_week(message: types.Message) -> None:
    student: db.UserModel | None = db.get_user_by_id(message.from_user.id)
    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        result: list[list[timetable.Lesson]] = await timetable.parse_week(
            student.group_name, student.subgroup
        )
        await message.answer(timetable.format_week(result))


@dp.message_handler(text="Назад")
async def go_back(message: types.Message) -> None:
    await message.answer("Вы в меню.", reply_markup=keyboards.menu_board)


@dp.message_handler(text="Четная неделя")
async def timetable_week_even(message: types.Message) -> None:
    student: db.UserModel | None = db.get_user_by_id(message.from_user.id)
    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        result: list[list[timetable.Lesson]] = await timetable.parse_week(
            student.group_name, student.subgroup, 1
        )
        await message.answer(timetable.format_week(result))


@dp.message_handler(text="Нечетная неделя")
async def timetable_week_odd(message: types.Message) -> None:
    student: db.UserModel | None = db.get_user_by_id(message.from_user.id)
    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        result: list[list[timetable.Lesson]] = await timetable.parse_week(
            student.group_name, student.subgroup, 2
        )
        await message.answer(timetable.format_week(result))


@dp.message_handler(text="Назад")
async def timetable_sequence_end(_message: types.Message) -> None:
    pass


# endregion -- Timetable


@dp.message_handler(text=emojize("Авторизоваться :rocket:"))
async def auth(message: types.Message) -> None:
    if not db.is_authenticated(message.from_user.id):
        await UserDataInputState.login.set()
        await message.answer(
            "Введите ваш логин для входа на usport.\nПример: NSurname-UG24"
        )
    else:
        await message.answer(
            "Вы уже авторизованы. Если хотите перезайти, нажмите 'Перезайти'.",
            reply_markup=keyboards.logoff_choice_board,
        )


@dp.message_handler(text="Назад")
async def go_back(message: types.Message) -> None:
    await message.answer("Вы в меню.", reply_markup=keyboards.menu_board)


@dp.message_handler(text="Перезайти")
async def relogin(message: types.Message) -> None:
    await UserDataInputState.login.set()
    await message.answer(
        "Введите ваш логин для входа на usport.\nПример: NSurname-UG24"
    )


# region    -- Input profile data
# TODO: make an logoff handler
@dp.message_handler(state=UserDataInputState.login)
async def add_login(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["login"] = format_sfu_login(message.text)
        if not data["login"]:
            await message.answer("Ошибка! Некоректный логин, попробуйте снова")
            return

        db.from_sfu_login(message.from_user.id, data["login"])
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

        db.add_group_to(message.from_user.id, data["group"])
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

        db.add_subgroup_to(message.from_user.id, data["subgroup"])
        await message.answer("Вы авторизованы!", reply_markup=keyboards.menu_board)
        await state.finish()


# endregion -- Input profile data


def start() -> None:
    executor.start_polling(dp, skip_updates=True)
