from parser import timetable, usport
from typing import Any

import database as db
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.app import keyboards
from emoji import emojize

from config import ADMIN_ID, TELEGRAM_TOKEN

bot: Bot = Bot(token=TELEGRAM_TOKEN)
dp: Dispatcher = Dispatcher(bot, storage=MemoryStorage())


class UserDataInputState(StatesGroup):
    login = State()
    group = State()
    subgroup = State()


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message) -> None:
    await message.reply(
        "Добро пожаловать, авторизуйтесь для начала работы.",
        reply_markup=keyboards.menu_board,
    )
    db.create_empty_profile(message.from_user.id)


# region    -- Usport
@dp.message_handler(text=emojize("Отметиться на физру :person_cartwheeling:"))
async def pe_qr(message: types.Message) -> None:
    telegram_id: str = message.from_user.id
    student: tuple[Any] | None = db.find_profile(telegram_id)

    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        await bot.send_photo(
            chat_id=message.chat.id, photo=usport.get_pe_qr_url(student[1])
        )


# endregion -- Usport


# region    -- Timetable
@dp.message_handler(text=emojize("Что сегодня? :student:"))
async def timetable_today(message: types.Message) -> None:
    student: tuple[Any] | None = db.find_profile(message.from_user.id)
    print(student)
    if student is None:
        await message.answer("Ошибка! Вы не авторизовались")
    else:
        result: list[timetable.Lesson] = await timetable.parse_today(student[2], student[3])
        await message.answer(f"\n{'-' * 60}\n".join(map(lambda x: str(x), result)))


@dp.message_handler(text=emojize("Расписание :teacher:"))
async def timetable_sequence_start(message: types.Message) -> None:
    await message.answer("Выберите неделю.", reply_markup=keyboards.timetable_board)


@dp.message_handler(text="Эта неделя")
async def timetable_this_week(message: types.Message) -> None:
    await message.answer("расписание занятий на эту неделю")


@dp.message_handler(text="Четная неделя")
async def timetable_week_even(message: types.Message) -> None:
    # расписание занятий по четным неделям
    await message.answer("расписание занятий по четным неделям")


@dp.message_handler(text="Нечетная неделя")
async def timetable_week_odd(message: types.Message) -> None:
    # расписание занятий по нечетным неделям
    await message.answer("расписание занятий по нечетным неделям")


@dp.message_handler(text="Назад")
async def timetable_sequence_end(message: types.Message) -> None:
    # расписание занятий по нечетным неделям
    await message.answer("ладно", reply_markup=keyboards.menu_board)


# endregion -- Timetable


@dp.message_handler(text=emojize("Авторизоваться :rocket:"))
async def auth(message: types.Message) -> None:
    await UserDataInputState.login.set()
    await message.answer(
        "Введите ваш логин для входа на usport.\n\
                         Пример: NSurname-UG24"
    )


# region    -- Input profile data
@dp.message_handler(state=UserDataInputState.login)
async def add_login(message: types.Message, state: FSMContext) -> None:
    # TODO: insert new user when add login is called?
    db.create_empty_profile(message.from_user.id)

    async with state.proxy() as data:
        data["login"] = message.text
        db.add_login(message.from_user.id, data["login"])

    await message.answer("Теперь введите название вашей группы\nПример: ВГ24-01Б")
    await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.group)
async def add_group(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["group"] = message.text
        db.add_group_name(message.from_user.id, data["group"])

    await message.answer("Введите номер вашей подгруппы (просто число).")
    await UserDataInputState.next()


@dp.message_handler(state=UserDataInputState.subgroup)
async def add_subgroup(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["subgroup"] = message.text
        db.add_subgroup_name(message.from_user.id, data["subgroup"])
    await message.answer("Вы авторизованы!")
    await state.finish()
# endregion -- Input profile data


def start() -> None:
    executor.start_polling(dp, skip_updates=True)
