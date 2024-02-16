# TODO: somehow implement cache to avoid parsing the same timetable every time?
from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum
from urllib import parse

import aiohttp
import pytz

SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")
BASE_URL = "https://edu.sfu-kras.ru/api/timetable/get"
BASE_URL_FORMAT = BASE_URL + "?target={group_name} ({subgroup_name} подгруппа)"
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
    # TODO: add link to map?
    full_location: str
    building: str
    room: str
    teacher: str
    is_sync: bool

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
            is_sync=(json.get("sync", "синхронно") == "синхронно"),
        )


def format_day(day: list[Lesson]) -> str:
    return f"\n\n".join(map(lambda x: str(x), day))


def format_week(week: list[list[Lesson]]) -> str:
    result: str = ""
    i: int = 0

    for day_name in [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
    ]:
        day_name: str
        if i == len(week):
            continue

        result += f"{day_name}\n"
        result += format_day(week[i]) + f"\n{'-' * 60}\n"
        i += 1
    return result


async def parse_today(group_name: str, subgroup_name: str) -> list[Lesson]:
    result: list[Lesson] = []

    json = await _get_timetable_json_for(group_name, subgroup_name)
    # Even/Odd week; day num
    _date_now = datetime.now(SFU_UNI_TIMEZONE)
    today_day_num: int = _date_now.weekday() + 1
    target_week_num: str = str(_get_week_num(_date_now))

    for item in json.get("timetable", []):
        item: dict
        day_num = int(item.get("day"))

        if day_num == today_day_num and item.get("week", "1") == target_week_num:
            result.append(Lesson.from_json(item))
        elif day_num > today_day_num:
            break

    return result


async def parse_week(
    group_name: str, subgroup_name: str, force_target_week_num: int = -1
) -> list[list[Lesson]]:
    result: list[list[Lesson]] = []

    json = await _get_timetable_json_for(group_name, subgroup_name)
    # Even/Odd week; day num
    index: int = 0
    target_week_num: str
    if force_target_week_num == -1:
        target_week_num = str(_get_week_num(datetime.now(SFU_UNI_TIMEZONE)))
    else:
        target_week_num = str(force_target_week_num)

    for item in json.get("timetable", []):
        item: dict
        day_num = int(item.get("day"))

        if day_num == index + 1:
            if item.get("week", "1") == target_week_num:
                if index not in result:
                    result.append([])
                result[index].append(Lesson.from_json(item))
        else:
            index += 1

    return result


def _get_week_num(now_datetime: datetime) -> int:
    """@return: 1 - even week; 2 - odd week"""
    return (now_datetime.day // 7 + 1) % 2 + 1


async def _get_timetable_json_for(group_name: str, subgroup_name: str) -> dict:
    url: str = BASE_URL_FORMAT.format(
        group_name=group_name, subgroup_name=subgroup_name
    )
    encoded = parse.urlencode(parse.parse_qs(parse.urlparse(url).query), doseq=True)
    url = "{}&{}".format(BASE_URL, encoded)

    async with aiohttp_session.get(url) as response:
        return await response.json()
