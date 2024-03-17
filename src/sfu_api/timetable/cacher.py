import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from . import img_generator
from parser import Lesson, ODD_DAY_NUM, EVEN_DAY_NUM, parse_week


UPDATE_EVERY_N_MINUTES: int = 60 * 24
cache_scheduler = BackgroundScheduler()
# Key - (group: str, subgroup: str)
# Value - dict[
#   specific_week_num: int, week_timetable: list[list[lessons]]
# ], where:
# - specific_week_num: ONLY either parser.EVEN_DAY_NUM or parser.ODD_DAY_NUM
_global_cache: dict[
	tuple[str, str], dict[int, list[list[Lesson]]]
] = {}


def init_cache_scheduler() -> None:
	cache_scheduler.add_job(
		update_timetable_cache, "interval",
		minutes=UPDATE_EVERY_N_MINUTES, id="timetable_cache_update"
	)
	cache_scheduler.start()
	week_cache.clear()


async def update_timetable_cache() -> None:
	global _global_cache

	# FIXME: TODO: CRITICAL:
	# At some point old (group, subgroup) entries inside _global_cache might become obsolete,
	# making timetable module parse incorrect data again, again and again...
	# NOTE: Solution - only delete old data ignoring previous cache entries? 
	keys = list(_global_cache.keys()).copy()
	# Clear old data
	_global_cache.clear()
	img_generator.delete_all()
	# Get new one for all previous cache entries
	for data in keys:
		group, subgroup = data
		group: str; subgroup: str

		even_week: list[list[Lesson]] | None = await parse_week(group, subgroup, EVEN_DAY_NUM)
		if even_week is not None:
			_put_week(group, subgroup, EVEN_DAY_NUM, even_week)
		else:
			logging.error("Cache update error! Can't parse even week for %s, %s", group, subgroup)
		
		odd_week: list[list[Lesson]] | None = await parse_week(group, subgroup, ODD_DAY_NUM)
		if odd_week is not None:
			_put_week(group, subgroup, ODD_DAY_NUM, odd_week)
		else:
			logging.error("Cache update error! Can't parse odd week for %s, %s", group, subgroup)


def try_get_day(group: str, subgroup: str, week_num: int, day_index: int) -> list[Lesson] | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	week_data: list[list[Lesson]] | None = try_get_week(group, subgroup, week_num)
	if week_data is None:
		return None
	
	return week_data[day_index]


def try_get_week(group: str, subgroup: str, week_num: int) -> list[list[Lesson]] | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	return _global_cache.get((group, subgroup), {}).get(week_num, None)


async def try_put_week(group: str, subgroup: str, week_num: int, data: Optional[list[list[Lesson]]] = None) -> None:
	"""
	1) Attempts to update cache either by using specified data or by parsing it.
	2) If update was successful, _put_week will call image generator
	@param data: If specified used as a value for cache update
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""

	if data is None:
		new_data: list[list[Lesson]] | None = await parse_week(group, subgroup, week_num)
		if new_data is not None:
			_put_week(group, subgroup, week_num, new_data)
		else:
			logging.error("Cache update error! Can't parse week for %s, %s", group, subgroup)
	else:
		_put_week(group, subgroup, week_num, data)


def _put_week(group: str, subgroup: str, week_num: int, data: list[list[Lesson]]) -> None:
	"""
	Updates global cache with specified data and calls image generator
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	global _global_cache
	
	if (group, subgroup) not in _global_cache:
		_global_cache[(group, subgroup)] = {}
	
	_global_cache[(group, subgroup)][week_num] = data

	for i in range(len(data)):
		img_generator.generate_all_day(group, subgroup, week_num, i, data[i])
