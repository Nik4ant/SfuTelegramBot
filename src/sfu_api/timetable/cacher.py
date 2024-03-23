import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from . import img_generator
from .common import *


UPDATE_EVERY_N_MINUTES: int = 60 * 24
cache_scheduler = BackgroundScheduler()
# Key - (group: str, subgroup: str)
# Value - dict[
#   specific_week_num: int, timetable_images: dict[int, str]
# ], where:
# - specific_week_num: ONLY either EVEN_DAY_NUM or ODD_DAY_NUM
# - key for timetable_images is day num from 0 to 6
# (Note: using dict for timetable_images because insertion in order is not guaranteed)
_global_cache: dict[
	tuple[str, str], dict[int, dict[int, list[str]]]
] = {}


def init_cache_scheduler() -> None:
	cache_scheduler.add_job(
		reset_global_cache, "interval",
		minutes=UPDATE_EVERY_N_MINUTES, id="timetable_cache_update"
	)
	cache_scheduler.start()
	reset_global_cache()


def reset_global_cache() -> None:
	global _global_cache
	
	_global_cache.clear()
	img_generator.delete_all()
	# Note: It's tempting to re-parse and re-generate all the data based on previous entries.
	# However at some point old (group, subgroup) entries inside _global_cache might become obsolete,
	# parsing incorrect data again, again and again + keeping garbage data around...
	# SO NEVER EVER DO THAT!


def try_get_day(group: str, subgroup: str, week_num: int, day_index: int) -> str | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	week_data: list[str] | None = try_get_week(group, subgroup, week_num)
	if week_data is None:
		return None
	
	# week_data isn't guaranteed to have data for ALL days
	if day_index >= len(week_data):
		return None
	return week_data[day_index]


def try_get_week(group: str, subgroup: str, week_num: int) -> list[str] | None:
	"""
	@param week_num: MUST be either EVEN_DAY_NUM or ODD_DAY_NUM
	"""
	days: dict[int, list[str]] | None = _global_cache.get((group, subgroup), {}).get(week_num, None)
	if days is not None:
		return list(days.values())
	return None


def put_week(days: list[Day]) -> list[str]:
	"""@return: Paths to timetable images added to the cache"""
	return [put_day(day) for day in days]


def put_day(day: Day) -> str:
	global _global_cache
	
	key: tuple[str, str] = (day.for_group, day.for_subgroup)

	if key not in _global_cache:
		_global_cache[key] = {}
	
	if day.week_num not in _global_cache[key]:
		_global_cache[key][day.week_num] = {}
	
	new_img: str = img_generator.generate_day(day)
	_global_cache[key][day.week_num][day.day_num] = new_img
	return new_img
