from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import aiohttp
from urllib import parse

from . import cacher
import img_generator
from config import SFU_UNI_TIMEZONE


BASE_URL = "https://edu.sfu-kras.ru/api/timetable/get"
BASE_URL_FORMAT = BASE_URL + "?target={group_name} (подгруппа {subgroup_name})"
CURRENT_DAY_NUM: int = -1
EVEN_DAY_NUM: int = 1
ODD_DAY_NUM: int = 2
aiohttp_session = aiohttp.ClientSession()


class LessonType(StrEnum):
	LECTURE = "лекция"
	PRACTISE = "пр. занятие"
	LAB = "лаб. работа"


@dataclass
class Lesson:
	name: str
	class_type: LessonType
	# for example, 08:30-10:05
	duration_time: str
	# TODO: add link to map/call/whatever?
	full_location: str
	building: str
	room: str
	teacher: str
	# "синхронно", "асинхронно", "ЭИОС"
	sync_status: str

	def __str__(self):
		return f"{('[' + self.class_type + ']') : <12} {self.duration_time : <12} {self.name}\n{self.teacher : <32}{self.full_location}"

	@classmethod
	def from_json(cls, json: dict):
		return Lesson(
			name=json.get("subject", ""),
			teacher=json.get("teacher", ""),
			full_location=json.get("place", ""),
			room=json.get("room", ""),
			building=json.get("building", ""),
			duration_time=json.get("time", ""),
			class_type=LessonType(json.get("type", "лекция")),
			is_sync=json.get("sync", "синхронно"),
		)


# TODO: DON'T FORGET! 
async def parse_today(group_name: str, subgroup_name: str) -> str | None:
	"""
	@return: Path to image file with timetable for today; None - if something went wrong
	"""
	result: list[Lesson] = []

	# Even/Odd week + day num
	_date_now = datetime.now(SFU_UNI_TIMEZONE)
	today_day_num: int = _date_now.weekday() + 1
	target_week_num: str = str(_get_week_num(_date_now))

	cache_data: list[Lesson] | None = cacher.try_get_day(group_name, subgroup_name, int(target_week_num), today_day_num)
	if cache_data is not None:
		# img already exists
		return img_generator.try_get_day(group_name, subgroup_name, int(target_week_num), today_day_num)

	json: dict | None = await _get_timetable_json_for(group_name, subgroup_name)
	if json is None:
		return None

	for item in json.get("timetable", []):
		item: dict
		day_num = int(item.get("day"))

		if day_num == today_day_num and item.get("week", "1") == target_week_num:
			result.append(Lesson.from_json(item))
		elif day_num > today_day_num:
			break
	
	# NOTE: This will force cache to load an entire week rather than 1 day
	cacher.try_put_week(group_name, subgroup_name, int(target_week_num), today_day_num, None)
	return img_generator.try_get_day(group_name, subgroup_name, int(target_week_num), today_day_num)


async def parse_week(
	group_name: str, subgroup_name: str, force_target_week_num: int = CURRENT_DAY_NUM
) -> list[str] | None:
	"""
	Parses timetable for current/specified week.
	@param force_target_week_num: Optional week number (1 - even; 2 - odd; -1 - current. See constants)
	@return: Path to generated images; None - if something went wrong
	"""
	result: list[list[Lesson]] = []

	# Even/Odd week
	index: int = 0
	target_week_num: str
	if force_target_week_num == -1:
		target_week_num = str(_get_week_num(datetime.now(SFU_UNI_TIMEZONE)))
	else:
		target_week_num = str(force_target_week_num)
	
	cache_data: list[list[Lesson]] | None = cacher.try_get_week(group_name, subgroup_name, int(target_week_num))
	if cache_data is not None:
		# images already exist
		return img_generator.try_get_week(group_name, subgroup_name, int(target_week_num))

	json: dict | None = await _get_timetable_json_for(group_name, subgroup_name)
	if json is None:
		return result

	for item in json.get("timetable", []):
		item: dict
		day_num = int(item.get("day"))

		# TODO: clean up this mess somehow? (or at least explain it?)
		if day_num == index + 1:
			if item.get("week", "1") == target_week_num:
				if index not in result:
					result.append([])
				result[index].append(Lesson.from_json(item))
		else:
			index += 1
			if day_num == index + 1:
				if item.get("week", "1") == target_week_num:
					if index not in result:
						result.append([])
					result[index].append(Lesson.from_json(item))

	cacher.put_week(group_name, subgroup_name, target_week_num, result)
	return img_generator.try_get_week(group_name, subgroup_name, int(target_week_num))


def _get_week_num(now_datetime: datetime) -> int:
	"""@return: 1 - even week; 2 - odd week"""
	return (now_datetime.day // 7) % 2 + 1


async def _get_timetable_json_for(group_name: str, subgroup_name: str) -> dict | None:
	url: str = BASE_URL_FORMAT.format(
		group_name=group_name, subgroup_name=subgroup_name
	)
	encoded = parse.urlencode(parse.parse_qs(parse.urlparse(url).query), doseq=True)
	url = "{}&{}".format(BASE_URL, encoded)
	try:
		async with aiohttp_session.get(url) as response:
			if response.status == 200:
				return await response.json()
			logging.error(f"Error {response.status} while calling SFU API `{url}`")
	except aiohttp.ClientError as e:
		logging.error(f"Failed to call SFU API `{url}`", exec_info=e)
	
	return None


async def close_http_session() -> None:
	await aiohttp_session.close()
