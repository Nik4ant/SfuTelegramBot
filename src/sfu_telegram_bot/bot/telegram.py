from emoji import emojize, demojize
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import date

from config import TELEGRAM_TOKEN, ADMIN_ID
from app import keyboards
import database as db

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class UserData(StatesGroup):
    login = State()
    group = State()
    subgroup = State()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Добро пожаловать, авторизуйтесь для начала работы.",
                        reply_markup=keyboards.menu_board)
    await db.create_db()
    await db.create_profile(message.from_user.id)
    
@dp.message_handler(text=emojize('Что сегодня? :student:'))
async def today(message: types.Message):
    # расписание занятий на сегодня
    await message.answer('расписание занятий на сегодня')
    pass

@dp.message_handler(text=emojize('Отметиться на физру :person_cartwheeling:'))
async def pe(message: types.Message):
    await message.answer('QR-код для физры')

@dp.message_handler(text=emojize('Расписание :teacher:'))
async def timetable(message: types.Message):
    await message.answer('Выберите неделю.', reply_markup=keyboards.timetable_board)

@dp.message_handler(text='Эта неделя')
async def this_week(message: types.Message):
    # расписание занятий на эту неделю
    await message.answer('расписание занятий на эту неделю')
    pass

@dp.message_handler(text='Четная неделя')
async def today(message: types.Message):
    # расписание занятий по четным неделям
    await message.answer('расписание занятий по четным неделям')
    pass

@dp.message_handler(text='Нечетная неделя')
async def today(message: types.Message):
    # расписание занятий по нечетным неделям
    await message.answer('расписание занятий по нечетным неделям')
    pass

@dp.message_handler(text='Назад')
async def today(message: types.Message):
    # расписание занятий по нечетным неделям
    await message.answer('ладно', reply_markup=keyboards.menu_board)
    pass




@dp.message_handler(text=emojize('Авторизоваться :rocket:'))
async def auth(message: types.Message):
    await UserData.login.set()
    await message.answer('Введите ваш логин для входа на usport.\n\
                         Пример: NSurname-UG24')

@dp.message_handler(state=UserData.login)
async def add_group(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['login'] = message.text
        await db.edit_profile('Добавить логин', message.from_user.id, data['login'])
    await message.answer('Теперь введите название вашей группы\nПример: ВГ24-01')
    await UserData.next()

@dp.message_handler(state=UserData.group)
async def add_group(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['group'] = message.text
        await db.edit_profile('Добавить группу', message.from_user.id, data['group'])
    await message.answer('Введите номер вашей подгруппы (просто число).')
    await UserData.next()

@dp.message_handler(state=UserData.subgroup)
async def add_subgroup(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['subgroup'] = message.text
        await db.edit_profile('Добавить подгруппу', message.from_user.id, data['subgroup'])
        await db.edit_profile('Set data', message.from_user.id, date.today().isoformat())
    await message.answer('Вы авторизованы!')
    await state.finish()
    


def start() -> None:
    executor.start_polling(dp, skip_updates=True)
