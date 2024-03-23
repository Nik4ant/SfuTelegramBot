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
	telegram_id: int = ""
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


# region    -- Profiles
def create_or_replace_user(telegram_id: int, sfu_login: str, group: str, subgroup: str) -> UserModel | None:
	"""@return: Returns None - if error occurred"""
	try:
		_now = datetime.now(SFU_UNI_TIMEZONE)
		cur.execute(
			"INSERT OR REPLACE INTO profiles VALUES(?, ?, ?, ?, ?)",
			(
				telegram_id,
				sfu_login,
				group,
				subgroup,
				_now,
			),
		)
		db.commit()
		logging.info(f"New user with for id: {telegram_id}, login `{sfu_login}`")
		return UserModel(
			telegram_id=telegram_id, sfu_login=sfu_login, last_time_interaction=_now
		)
	except sql.Error as err:
		logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
		return None


def update_interaction_time_for(telegram_id: int) -> None:
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
# endregion -- Profiles


# region    -- Search/Delete
def get_user_if_authenticated(telegram_id: int) -> UserModel | None:
	"""@return: User only if ALL fields are present; None - otherwise"""
	
	try:
		cur.execute("SELECT * FROM profiles WHERE telegram_id == ?", (telegram_id,))
		data: tuple[Any] | None = cur.fetchone()
		
		if data == None:
			return None
		
		for part in data:
			if part is None:
				return None
		return UserModel.from_db_tuple(data)
	except sql.Error as err:
		logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
		return None


def remove_old_profiles() -> None:
	try:
		cur.execute(
			"DELETE FROM profiles WHERE date(last_time_interaction) <= date('now', '-1 years')"
		)
		db.commit()
	except sql.Error as err:
		logging.exception(f"SQL error: {err.sqlite_errorname}", exc_info=err)
		return None
# endregion -- Search/Delete
