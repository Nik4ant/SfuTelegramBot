from aiogram import Bot, Dispatcher, executor, types
from config import ADMIN_ID, TELEGRAM_SUPPORT_TOKEN

bot: Bot = Bot(token=TELEGRAM_SUPPORT_TOKEN)
dp: Dispatcher = Dispatcher(bot)


async def is_admin(id: int) -> bool:  # ADMIN ID CHECKER
    if id == int(ADMIN_ID):
        return True
    return False


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message) -> None:
    if await is_admin(message.from_user.id):
        await message.reply(f"Добро пожаловать, {message.from_user.first_name}!")


async def send_message(message) -> None:
    await bot.send_message(int(ADMIN_ID), message)


def start() -> None:
    executor.start_polling(dp, skip_updates=True)
