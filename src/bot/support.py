from aiogram import Bot, Dispatcher, executor, types

from config import ADMIN_IDS, TELEGRAM_SUPPORT_TOKEN
from validation import is_admin


bot: Bot = Bot(token=TELEGRAM_SUPPORT_TOKEN)
dp: Dispatcher = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message) -> None:
    if is_admin(message.from_user.id):
        await message.reply(f"Добро пожаловать, {message.from_user.first_name}!")


async def send_message(message) -> None:
    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id, message)


def start() -> None:
    executor.start_polling(dp, skip_updates=True)


async def close() -> None:
    await bot.close_bot()
