import aiosqlite

DB_NAME = 'quiz_bot.db'


async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        # Сохраняем изменения
        await db.commit()


async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()


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


async def create_correct_answers():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (user_id INTEGER PRIMARY KEY, correct_answers INTEGER)''')
        await db.commit()


async def update_correct_answers(user_id, correct_answers):
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, есть ли запись для данного пользователя
        cursor = await db.execute('''SELECT * FROM quiz_results WHERE user_id = ?''', (user_id,))
        result = await cursor.fetchone()
        if result is None:
            # Если записи нет, создаем новую
            await db.execute('''INSERT INTO quiz_results (user_id, correct_answers) VALUES (?, ?)''', (user_id, correct_answers))
        else:
            # Если запись есть, обновляем количество правильных ответов
            if correct_answers == 0:
                # Если количество правильных ответов равно 0, обнуляем его
                await db.execute('''UPDATE quiz_results SET correct_answers = 0 WHERE user_id = ?''', (user_id,))
            else:
                # В противном случае увеличиваем количество правильных ответов
                await db.execute('''UPDATE quiz_results SET correct_answers = correct_answers + ? WHERE user_id = ?''', (correct_answers, user_id))
        await db.commit()

async def get_correct_answers(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''SELECT correct_answers FROM quiz_results WHERE user_id = ?''', (user_id,))
        result = await cursor.fetchone()
        if result is None:
            return 0
        else:
            return result[0]

async def reset_result(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, есть ли запись для данного пользователя
        cursor = await db.execute('''SELECT * FROM quiz_results WHERE user_id = ?''', (user_id,))
        result = await cursor.fetchone()
        if result is not None:
            # Если запись есть, обновляем количество правильных ответов
            await db.execute('''UPDATE quiz_results SET correct_answers = 0 WHERE user_id = ?''', (user_id,))
        await db.commit()
