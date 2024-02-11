import asyncio

from aiogram import Bot, Dispatcher, executor, types

from config import TELEGRAM_TOKEN


# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message) -> None:
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler()
async def echo(message: types.Message) -> None:
    await message.answer(message.text)


def start() -> None:
    executor.start_polling(dp, skip_updates=True)
