import aiosqlite
import quiz_data as quiz_data
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types, Dispatcher

# Зададим имя базы данных
DB_NAME = 'quiz_bot.db'

# Диспетчер
dp = Dispatcher()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):


    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    # получаем текущий результат пользователя из базы данных
    current_result = await get_last_result(callback.from_user.id)
    current_result += 1
    await update_quiz_index_and_result(callback.from_user.id, current_question_index, current_result)
    if current_question_index < len(quiz_data.quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):


    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data.quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data.quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    current_result = await get_last_result(callback.from_user.id)
    current_result += 0
    await update_quiz_index_and_result(callback.from_user.id, current_question_index, current_result)


    if current_question_index < len(quiz_data.quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


async def get_question(message, user_id):
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data.quiz_data[current_question_index]['correct_option']
    opts = quiz_data.quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data.quiz_data[current_question_index]['question']}", reply_markup=kb)



async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    current_last_result = 0
    await update_quiz_index_and_result(user_id, current_question_index, current_last_result)
    await get_question(message, user_id)


async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def get_last_result(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT last_result FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is None:
                return 0
            else:
                return results[0]


async def update_quiz_index_and_result(user_id, index, result):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, last_result) VALUES (?, ?, ?)', (user_id, index, result))
        # Сохраняем изменения
        await db.commit()


async def get_player_stats():
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Получаем все записи из таблицы quiz_state
        async with db.execute('SELECT user_id, last_result FROM quiz_state') as cursor:
            # Возвращаем результат
            results = await cursor.fetchall()
            return results


async def create_table():
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
                         user_id INTEGER PRIMARY KEY, 
                         question_index INTEGER, 
                         last_result INTEGER)''')
        # Сохраняем изменения
        await db.commit()