import aiosqlite

DB_NAME = 'config.db'

async def get_config(key):
    query = 'SELECT value FROM config WHERE key = ?'
    bind = (key,)

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, bind)
            rows = await cursor.fetchall()
            await cursor.close()

            return [row['value'] for row in rows]

    except Exception as e:
        print('Failed to get config:')
        print(e, key)
        return False

async def set_config(key, value):
    query = 'UPDATE config SET value = ? WHERE key = ?'
    bind = (value, key)

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(query, bind)
            await db.commit()
        return True
    except Exception as e:
        print('Failed to update config value:')
        print(e, key, value)
        return False

async def add_config(key, value):
    query = 'INSERT INTO config (key, value) VALUES (?, ?)'
    bind = (key, value)

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(query, bind)
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add config value:')
        print(e, key, value)
        return False

async def remove_config(key, value):
    query = 'DELETE FROM config WHERE key = ? and value = ?'
    bind = (key, value)

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(query, bind)
            await db.commit()
        return True
    except Exception as e:
        print('Failed to remove config value:')
        print(e, key, value)
        return False
