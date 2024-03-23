import aiohttp
from urllib import parse

from . import cacher, img_generator
from .common import *
from config import SFU_UNI_TIMEZONE


BASE_URL = "https://edu.sfu-kras.ru/api/timetable/get"
# NOTE: Apparently Sfu api HAS 2 DIFFERENT URL VARIANTS FOR THE SAME ENDPOINT?!?!
# O_o. If something goes wrong, there is a chance that it's another url variant -_-
URL_VARIANTS: list[str] = [
	BASE_URL + "?target={group_name} ({subgroup_name} подгруппа)",
	BASE_URL + "?target={group_name} (подгруппа {subgroup_name})",
]
aiohttp_session = aiohttp.ClientSession()


async def parse_today(group_name: str, subgroup_name: str) -> str | None:
	"""
	@return: Path to image file with timetable for today; None - if something went wrong
	"""
	lessons: list[Lesson] = []

	# Even/Odd week + day num
	_date_now = datetime.now(SFU_UNI_TIMEZONE)
	today_day_num: int = _date_now.weekday() + 1
	target_week_num: str = str(_get_week_num(_date_now))

	result: Day = Day(today_day_num - 1, int(target_week_num), group_name, subgroup_name, [])

	cache_data: str | None = cacher.try_get_day(group_name, subgroup_name, int(target_week_num), today_day_num)
	if cache_data is not None:
		return cache_data

	json: dict | None = await _get_timetable_json_for(group_name, subgroup_name)
	if json is None:
		return None

	for item in json.get("timetable", []):
		item: dict
		day_num = int(item.get("day"))

		if day_num == today_day_num and item.get("week", "1") == target_week_num:
			lessons.append(Lesson.from_json(item))
		elif day_num > today_day_num:
			break
	
	result.lessons = lessons
	return cacher.put_day(result)


async def parse_week(
	group_name: str, subgroup_name: str, force_target_week_num: WeekNum = WeekNum.CURRENT
) -> list[str] | None:
	"""
	Parses timetable for current/specified week.
	@param force_target_week_num: Optional week number (See enum in common.py)
	@return: Path to generated images; None - if something went wrong
	"""
	result: list[Day] = []

	# Even/Odd week
	target_week_num: str
	if force_target_week_num == WeekNum.CURRENT:
		target_week_num = str(_get_week_num(datetime.now(SFU_UNI_TIMEZONE)))
	else:
		target_week_num = str(int(force_target_week_num))
	
	# NOTE: Thanks to cacher.put_day cache_data can contain any number of days.
	# Since there is no way to check how many days are suppose to be there
	# cache_data is used only if all 6 days are present
	# (Not ideal, but still better than returing wrong data)
	cache_data: list[str] | None = cacher.try_get_week(group_name, subgroup_name, int(target_week_num))
	if cache_data is not None and len(cache_data) == 6:
		return cache_data

	json: dict | None = await _get_timetable_json_for(group_name, subgroup_name)
	if json is None:
		return None

	cur_day_num: int = 0
	current_day: Day = Day(cur_day_num, int(target_week_num), group_name, subgroup_name, [])
	for item in json.get("timetable", []):
		item: dict
		day_num = int(item.get("day"))
		
		if day_num == cur_day_num + 1:
			if item.get("week", "1") == target_week_num:
				current_day.lessons.append(Lesson.from_json(item))
		# Finished parsing one day...
		else:
			cur_day_num += 1
			result.append(current_day)
			# Parse new one
			current_day = Day(
				cur_day_num, int(target_week_num), group_name, subgroup_name, []
			)
			if item.get("week", "1") == target_week_num:
				current_day.lessons.append(Lesson.from_json(item))
	# Final day
	result.append(current_day)
	return cacher.put_week(result)


def _get_week_num(now_datetime: datetime) -> int:
	if (now_datetime.day // 7) % 2:
		return int(WeekNum.EVEN)
	return int(WeekNum.ODD)


async def _get_timetable_json_for(group_name: str, subgroup_name: str) -> dict | None:
	for variant in URL_VARIANTS:
		url: str = variant.format(
			group_name=group_name, subgroup_name=subgroup_name
		)
		encoded = parse.urlencode(parse.parse_qs(parse.urlparse(url).query), doseq=True)
		url = "{}&{}".format(BASE_URL, encoded)
		try:
			async with aiohttp_session.get(url) as response:
				if response.status == 200:
					json: dict = await response.json()
					# If empty try next url variant...
					if len(json.get("timetable", [])) == 0:
						continue
					return json
				logging.error(f"Error {response.status} while calling SFU API `{url}`")
		except aiohttp.ClientError as e:
			logging.error(f"Failed to call SFU API `{url}`", exec_info=e)
	
	return None


async def close_http_session() -> None:
	await aiohttp_session.close()
