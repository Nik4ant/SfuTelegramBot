# TODO: somehow implement cache to avoid parsing the same timetable every time?
from datetime import datetime, time
from dataclasses import dataclass
from enum import StrEnum

import pytz
import aiohttp
from urllib import parse


# sfu logins use latin, API uses cyrillic -_-
LATIN_TO_RU: dict = {
    ord(a): ord(b) for a, b in zip(
        *(
            u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA",
            u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        )
    )
}
SFU_UNI_TIMEZONE = pytz.timezone("Asia/Krasnoyarsk")
BASE_URL = "https://edu.sfu-kras.ru/api/timetable/get"
BASE_URL_FORMAT = BASE_URL + "?target={group_name} ({subgroup_name} подгруппа)"
aiohttp_session = aiohttp.ClientSession()


class LessonType(StrEnum):
    LECTURE = "лекция"
    PRACTISE = "пр. занятие"
    LAB = "лаб. работа"


class Day(StrEnum):
    SUNDAY = "воскресенье"
    MONDAY = "понедельник"
    TUESDAY = "вторник"
    WEDNESDAY = "среда"
    THURSDAY = "четверг"
    FRIDAY = "пятница"
    SATURDAY = "суббота"


@dataclass
class Lesson:
    name: str
    class_type: LessonType
    # for example, 08:30-10:05
    duration_time: str
    # TODO: add link to map?
    location: str
    teacher: str
    is_sync: bool

    def __str__(self):
        return f"{('[' + self.class_type + ']') : <12} {self.duration_time : <12} {self.name}\n{self.teacher : <32}{self.location}"


async def parse_today(group_name: str, subgroup_name: str) -> list[Lesson]:
    result: list[Lesson] = []
    # TODO: error checks on EVERY step
    url: str = BASE_URL_FORMAT.format(group_name=group_name.translate(LATIN_TO_RU), subgroup_name=subgroup_name)
    encoded = parse.urlencode(
        parse.parse_qs(parse.urlparse(url).query),
        doseq=True
    )
    url = "{}&{}".format(BASE_URL, encoded)

    async with aiohttp_session.get(url) as response:
        data = await response.json()
        target_day_num: int = datetime.now(SFU_UNI_TIMEZONE).weekday() + 1
        for item in data.get("timetable", []):
            item: dict
            print(item)
            day_num = int(item.get("day"))
            # TODO: odd/even weeks + other stuff
            if day_num == target_day_num and item.get("week", '1') == '1':
                result.append(
                    Lesson(
                        name=item.get("subject", ''),
                        teacher=item.get("teacher", ''),
                        location=item.get("place", ''),
                        duration_time=item.get("time", ''),
                        class_type=LessonType(item.get("type", "лекция")),
                        is_sync=(item.get("sync", "синхронно") == "синхронно")
                    )
                )
            elif day_num > target_day_num:
                break

    return result
