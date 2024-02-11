import sqlite3 as sq


async def create_db(): # Создание базы данных
    global db, cur

    db = sq.connect('database.db')
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS profiles(
        user_ID TEXT PRIMARY KEY,
        login TEXT,
        gr TEXT,
        undergr TEXT,
        last_date DATEONLY
    )""")
    db.commit()


async def create_profile(user_ID): # Создание профиля с чистыми данными
    user = cur.execute(f"SELECT 1 FROM profiles WHERE user_ID == '{user_ID}'").fetchone()
    cur.execute("UPDATE profiles SET last_date = date('now')")

    if not user:
        cur.execute(f"INSERT INTO profiles VALUES({user_ID}, NULL, NULL, NULL, date('now'))")
        print("NEW USER")

    db.commit()


async def edit_profile(operation, user_ID, data=''): # Изменение данных у профиля
    if operation == "Очистить данные":
        cur.execute(f"UPDATE profiles SET login = NULL WHERE user_ID == '{user_ID}'")
        cur.execute(f"UPDATE profiles SET gr = NULL WHERE user_ID == '{user_ID}'")
        cur.execute(f"UPDATE profiles SET undergr = NULL WHERE user_ID == '{user_ID}'")

    elif operation == "Добавить логин":
        cur.execute(f"UPDATE profiles SET login = '{data}' WHERE user_ID == '{user_ID}'")

    elif operation == "Добавить группу":
        cur.execute(f"UPDATE profiles SET gr = '{data}' WHERE user_ID == '{user_ID}'")

    elif operation == "Добавить подгруппу":
        cur.execute(f"UPDATE profiles SET undergr = '{data}' WHERE user_ID == '{user_ID}'")
    db.commit()

async def find_profile(user_ID): # Ищет данные по профилю и возвращает картеж
    cur.execute(f"SELECT * from profiles WHERE user_ID == '{user_ID}'")
    return cur.fetchone()


async def remove_profiles(): # Смотрит последнюю дату входа всех профилей и удаляет старые профили
    cur.execute("DELETE FROM profiles WHERE date(last_date) <= date('now', '-1 years')")
    db.commit()
