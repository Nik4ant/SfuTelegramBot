import logging
import sqlite3 as sql
from dataclasses import dataclass
from datetime import datetime
from sys import exit
from typing import Any, Self

from config import SFU_UNI_TIMEZONE

db: sql.Connection = sql.connect("database.db", detect_types=sql.PARSE_DECLTYPES)
cur: sql.Cursor = db.cursor()


@dataclass
class UserModel:
    telegram_id: str = ""
    sfu_login: str = ""
    group_name: str = ""
    subgroup: str = ""
    last_time_interaction: datetime = datetime.now()

    @classmethod
    def from_db_tuple(cls, data: tuple[Any]) -> Self | None:
        if len(data) != 5:
            logging.error(
                f"UserModel.from_db_tuple(...) was expecting 5 params, but got: {data}"
            )
            return None
        return UserModel(*data)

    def clear(self) -> Self | None:
        """@return: Returns None - if error occurred"""
        now = datetime.now(SFU_UNI_TIMEZONE)
        if clear_by_id(self.telegram_id, _sync_time_now=now):
            self.last_time_interaction = now
            return self

        return None

    def update_interaction_time(self) -> None:
        update_interaction_time_for(self.telegram_id)


def init_db() -> None:
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles
            (
                telegram_id TEXT PRIMARY KEY,
                sfu_login TEXT,
                group_name TEXT,
                subgroup TEXT,
                last_time_interaction DATEONLY
            )"""
        )
        db.commit()
    except sql.Error as err:
        logging.critical(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        exit(1)


# region    -- Init profiles
def empty(telegram_id: str) -> UserModel | None:
    """@return: Returns None - if error occurred"""
    try:
        _now = datetime.now(SFU_UNI_TIMEZONE)
        cur.execute(
            "INSERT INTO profiles VALUES(?, NULL, NULL, NULL, ?)",
            (
                telegram_id,
                _now,
            ),
        )
        db.commit()
        logging.info(f"New user with id: {telegram_id}")
        return UserModel(telegram_id=telegram_id, last_time_interaction=_now)
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return None


def from_sfu_login(telegram_id: str, sfu_login: str) -> UserModel | None:
    """@return: Returns None - if error occurred"""
    try:
        _now = datetime.now(SFU_UNI_TIMEZONE)
        cur.execute(
            "INSERT OR REPLACE INTO profiles VALUES(?, ?, NULL, NULL, ?)",
            (
                telegram_id,
                sfu_login,
                _now,
            ),
        )
        db.commit()
        logging.info(f"New user with id: {telegram_id} from login `{sfu_login}`")
        return UserModel(
            telegram_id=telegram_id, sfu_login=sfu_login, last_time_interaction=_now
        )
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return None


# endregion -- Init profiles


# region    -- Edit profiles
def add_group_to(telegram_id: str, group_name: str) -> None:
    cur.execute(
        "UPDATE profiles SET group_name = ?, last_time_interaction = ? WHERE telegram_id == ?",
        (group_name, datetime.now(SFU_UNI_TIMEZONE), telegram_id),
    )
    db.commit()


def add_subgroup_to(telegram_id: str, subgroup: str) -> None:
    cur.execute(
        "UPDATE profiles SET subgroup = ?, last_time_interaction = ? WHERE telegram_id == ?",
        (subgroup, datetime.now(SFU_UNI_TIMEZONE), telegram_id),
    )
    db.commit()


def update_interaction_time_for(telegram_id: str) -> None:
    if not telegram_id:
        logging.warning("Can't update interaction time for user with no telegram id!")
        return

    try:
        cur.execute(
            "UPDATE profiles SET last_time_interaction = ? WHERE telegram_id == ?",
            (
                datetime.now(SFU_UNI_TIMEZONE),
                telegram_id,
            ),
        )
        db.commit()
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)


# endregion -- Edit profiles


# region    -- Search/Clear/Delete
def get_user_by_id(telegram_id: str) -> UserModel | None:
    try:
        cur.execute("SELECT * from profiles WHERE telegram_id == ?", (telegram_id,))
        data: tuple[Any] | None = cur.fetchone()
        if data is None:
            return None
        return UserModel.from_db_tuple(data)
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return None


def user_exists(telegram_id: str) -> bool:
    return (
        cur.execute(
            "SELECT COUNT(1) FROM profiles WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()[0]
        != 0
    )


def is_authenticated(telegram_id: str) -> bool:
    cur.execute("SELECT * FROM profiles WHERE telegram_id == ?", (telegram_id,))
    data: tuple[Any] | None = cur.fetchone()
    if data == None:
        return False
    for elem in data:
        if elem != None:
            return True


def clear_by_id(telegram_id: str, _sync_time_now: datetime = None) -> bool:
    """
    @param _sync_time_now: If exists overrides last_time_interaction
    @return: True - if no errors occurred; False - otherwise
    """
    try:
        _now = (
            datetime.now(SFU_UNI_TIMEZONE) if _sync_time_now is None else _sync_time_now
        )

        cur.execute(
            """
            UPDATE profiles SET sfu_login = NULL, group_name = NULL, subgroup = NULL, last_time_interaction = ?
            WHERE telegram_id == ?
            """,
            (telegram_id, _now),
        )
        db.commit()

        logging.info(f"Cleared {telegram_id}'s info")
        return True
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return False


def remove_old_profiles() -> None:
    try:
        cur.execute(
            "DELETE FROM profiles WHERE date(last_time_interaction) <= date('now', '-1 years')"
        )
        db.commit()
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return None


def remove_by_id(telegram_id: str) -> None:
    try:
        cur.execute("DELETE FROM profiles WHERE telegram_id == ?", (telegram_id,))
        db.commit()
    except sql.Error as err:
        logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
        return None


# endregion -- Search/Delete
