from aiogram import Bot, Dispatcher, types
from aiogram import types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters.command import Command
from db import *
from questions import quiz_data
import settings


# Объект бота
bot = Bot(settings.API_TOKEN)
# Диспетчер
dp = Dispatcher()



@dp.message(Command("start"))
# Хэндлер на команду /start
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer(f'{message.from_user.first_name}, добро пожаловать в квиз!', reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f'Давай начнем квиз!')
    # Запускаем новый квиз
    await new_quiz(message)


async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    # сбрасываем значение результата квиза к 0
    await reset_result(user_id)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)


async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)
    # Увеличение количества правильных ответов в базе данных
    await update_correct_answers(callback.from_user.id, 1)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        correct_answers = await get_correct_answers(callback.from_user.id)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Количество правильных ответов: {correct_answers}")



@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)
    correct_answers = await get_correct_answers(callback.from_user.id)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Количество правильных ответов: {correct_answers}")


def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 4 Inline кнопки, а точнее Callback-кнопки
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            # Если ответ верный сформируется колбэк-запрос с данными 'right_answer'
            # Если ответ неверный сформируется колбэк-запрос с данными 'wrong_answer'
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()
