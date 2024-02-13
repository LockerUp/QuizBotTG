import logging
import QuizBotTG.database as database
from tabulate import tabulate
from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F
from QuizBotTG.database import dp

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '6869353805:AAFJYeAClF4DLFrrX0Y3Kdtxds0Vt1_SSX4'

# Объект бота
bot = Bot(token=API_TOKEN)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await database.new_quiz(message)


@dp.message(Command('stats'))
async def show_stats(message: types.Message):
    stats = await database.get_player_stats()
    if stats:
        table = tabulate(stats, headers=['User ID', 'Last Result'])  # создаем таблицу
        response = f"Player Statistics:\n{table}"
        await message.answer(response)
    else:
        await message.answer("No player statistics available.")



# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await database.create_table()

    await dp.start_polling(bot)