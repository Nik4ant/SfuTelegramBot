import logging
import sqlite3 as sql
from typing import Any

# Можно переместить это в init_db, а переменные оставить тут, нооооооо не
db: sql.Connection = sql.connect("database.db")
cur: sql.Cursor = db.cursor()


def init_db() -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles
        (
            telegram_id TEXT PRIMARY KEY,
            login TEXT,
            group_name TEXT,
            subgroup_name TEXT,
            last_change_date DATEONLY
        )"""
    )
    db.commit()


def create_empty_profile(telegram_id: str) -> None:
    cur.execute(
        "INSERT INTO profiles VALUES(?, NULL, NULL, NULL, date('now'))", (telegram_id,)
    )
    db.commit()
    logging.info(f"New user with id: {telegram_id}")


# region    -- Edit profile
# TODO: Что считается за вход? Добавление логина? Пока видимо да
# TODO: logging
# TODO: add a safe check def user_exists(id: str) -> bool
# TODO: change filewatcher to format
# TODO: автоматическое правило, которое будет обновлять last_change_date в SQL при UPDATE (см. триггеры и прочие штуки)
def update_date(telegram_id: str) -> None:
    cur.execute(
        "UPDATE profiles SET last_change_date = date('now') WHERE telegram_id == ?",
        (telegram_id,),
    )
    db.commit()


def clear_profile_data(telegram_id: str) -> None:
    cur.execute(
        """
        UPDATE profiles SET login = NULL, group_name = NULL, subgroup_name = NULL
        WHERE telegram_id == ?
        """,
        (telegram_id,),
    )
    db.commit()


def add_login(telegram_id: str, login: str) -> None:
    cur.execute(
        "UPDATE profiles SET login = ?, last_change_date = date('now') WHERE telegram_id == ?",
        (login, telegram_id),
    )
    db.commit()


def add_group_name(telegram_id: str, group_name: str) -> None:
    cur.execute(
        "UPDATE profiles SET group_name = ?, last_change_date = date('now') WHERE telegram_id == ?",
        (group_name, telegram_id),
    )
    db.commit()


def add_subgroup_name(telegram_id: str, subgroup_name: str) -> None:
    cur.execute(
        "UPDATE profiles SET subgroup_name = ?, last_change_date = date('now') WHERE telegram_id == ?",
        (subgroup_name, telegram_id),
    )
    db.commit()


# endregion -- Edit profile


def profile_exists(telegram_id: str) -> bool:
    return (
        cur.execute(
            "SELECT COUNT(1) FROM profiles WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()[0]
        != 0
    )


# TODO: вместо tuple возвращать объект User, чтобы там все поля были
def find_profile(telegram_id: str) -> tuple[Any] | None:
    cur.execute("SELECT * from profiles WHERE telegram_id == ?", (telegram_id,))
    return cur.fetchone()


def remove_old_profiles() -> None:
    cur.execute(
        "DELETE FROM profiles WHERE date(last_change_date) <= date('now', '-1 years')"
    )
    db.commit()
