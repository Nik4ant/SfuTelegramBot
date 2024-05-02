import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from . import img_generator
from .common import *


UPDATE_EVERY_N_MINUTES: int = 60 * 24
cache_scheduler = BackgroundScheduler()
# NOTE: Yeap, cache doesn't work with the theme selection. To be fair such option doesn't exist anyway, so...
# (the real problem here is that cache holds raw strings to timetable images with no extra info...)
# NOTE 2: The fact that cache is split into day cache and week cache is wierd, buuuuut it's good enough
#  (as long as the note above isn't resolved)
_global_day_cache: dict[
	# (group: str, subgroup: str)
	tuple[str, str],
	dict[
		# key - specific_week_num: int (ONLY either EVEN_DAY_NUM or ODD_DAY_NUM)
		int,
		# value - week timetable images
		dict[
			# key - day_num: int (from 0 to 6)
			int,
			# value - image
			str
		]
	]
] = {}
_global_week_cache: dict[
	# (group: str, subgroup: str)
	tuple[str, str],
	# key - specific_week_num: int (ONLY either EVEN_DAY_NUM or ODD_DAY_NUM)
	# value - generated image
	dict[int, str]
] = {}


def init_cache_scheduler() -> None:
	cache_scheduler.add_job(
		reset_global_cache, "interval",
		minutes=UPDATE_EVERY_N_MINUTES, id="timetable_cache_update"
	)
	cache_scheduler.start()
	reset_global_cache()


def reset_global_cache() -> None:
	# Note: It's tempting to re-parse and re-generate all the data based on previous entries.
	# However at some point old (group, subgroup) entries inside _global_day_cache might become obsolete,
	# parsing incorrect data again, again and again + keeping garbage data around...
	# SO NEVER EVER DO THAT!
	global _global_day_cache, _global_week_cache
	
	_global_day_cache.clear()
	_global_week_cache.clear()
	img_generator.delete_all()


def try_get_day(group: str, subgroup: str, week_num: int, day_index: int) -> str | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	week_data: dict[int, str] | None = _global_day_cache.get((group, subgroup), {}).get(week_num, None)
	if week_data is None:
		return None
	
	# week_data isn't guaranteed to have data for ALL days
	return week_data.get(day_index, None)


def try_get_week(group: str, subgroup: str, week_num: int) -> str | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	return _global_week_cache.get((group, subgroup), {}).get(week_num, None)


def put_week(days: list[Day]) -> str:
	"""@return: Path to timetable image added to the cache"""
	global _global_week_cache

	key: tuple[str, str] = (days[0].for_group, days[0].for_subgroup)
	if key not in _global_week_cache:
		_global_week_cache[key] = {}

	new_img: str = img_generator.generate_week(days)
	_global_week_cache[key][days[0].week_num] = new_img
	return new_img


def put_day(day: Day) -> str:
	"""@return: Path to timetable image added to the cache"""
	global _global_day_cache
	
	key: tuple[str, str] = (day.for_group, day.for_subgroup)

	if key not in _global_day_cache:
		_global_day_cache[key] = {}
	
	if day.week_num not in _global_day_cache[key]:
		_global_day_cache[key][day.week_num] = {}
	
	new_img: str = img_generator.generate_day(day)
	_global_day_cache[key][day.week_num][day.day_num] = new_img
	return new_img
