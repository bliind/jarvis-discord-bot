import aiosqlite
import datetime

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

async def add_streaming_post(message_id, datestamp):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO streaming_post (message_id, datestamp) VALUES (?, ?)', (message_id, datestamp))
            await db.commit()
    except Exception as e:
        print(f'{timestamp()}: Failed to add streaming post:')
        print(e, message_id, datestamp)

async def get_old_streaming_posts(datestamp):
    posts = []
    try:
        async with aiosqlite.connect('db.db') as db:
            cursor = await db.execute('SELECT * FROM streaming_post WHERE datestamp <= ?', (datestamp,))
            async for row in cursor:
                posts.append(row[0])

    except Exception as e:
        print(f'{timestamp()}: Failed to get old streaming posts:')
        print(e, datestamp)

    return posts

async def delete_streaming_posts(message_ids):
    safe_string = ','.join(['?' for m in message_ids])
    sql = f'DELETE from streaming_post WHERE message_id IN ({safe_string});'

    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute(sql, message_ids)
            await db.commit()
    except Exception as e:
        print(f'{timestamp()}: Failed to delete streaming posts:')
        print(e, message_ids)

## Quiz stuff
async def create_quiz(message_id, quiz_name, correct_answer):
    try:
        datestamp = timestamp()
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO quiz (datestamp, message_id, quiz_name, correct_answer) VALUES (?, ?, ?, ?)', (datestamp, message_id, quiz_name, correct_answer))
            await db.commit()
        return True
    except Exception as e:
        print(f'{timestamp()}: Failed to add quiz:')
        print(e, datestamp, message_id, quiz_name, correct_answer)
        return False

async def check_quiz_answered(message_id, user_id):
    row = None
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM quiz_answer WHERE message_id = ? AND user_id = ?', (message_id, user_id))
            row = await cursor.fetchone()
    except Exception as e:
        print('Failed to check if user answered:')
        print(e, message_id, user_id)

    return row

async def record_quiz_answer(message_id, user_id, answer):
    try:
        datestamp = timestamp()
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO quiz_answer (datestamp, message_id, user_id, answer) VALUES (?, ?, ?, ?)', (datestamp, message_id, user_id, answer))
            await db.commit()
        return True
    except Exception as e:
        print(f'{timestamp()}: Failed to add quiz_answer:')
        print(e, datestamp, message_id, user_id, answer)
        return False

async def get_quiz_winners(message_id):
    sql = '''
        SELECT * FROM quiz_answer
        JOIN quiz ON quiz.message_id = quiz_answer.message_id
        WHERE quiz.correct_answer = quiz_answer.answer
        AND quiz.message_id = ?
    '''.replace(' '*8, '').strip()

    winners = []
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (message_id,))
            async for row in cursor:
                winners.append(row)

    except Exception as e:
        print(f'{timestamp()}: Failed to get quiz winners:')
        print(e, message_id)

    return winners
