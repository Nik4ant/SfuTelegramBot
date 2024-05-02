# Types, constants and other stuff shared by sfu_api/timetable
# (not perfect, but good enough)
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, IntEnum


class WeekNum(IntEnum):
	ODD = 1
	EVEN = 2
	CURRENT = -1


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
			sync_status=json.get("sync", "синхронно"),
		)


@dataclass()
class Day:
	# 0 - Monday, 6 - Sunday
	# (Although there are probably no classes on Sunday...)
	day_num: int
	week_num: WeekNum
	# - Is it a good idea to keep group info here?
	# - Probably not
	# - Does it solve a lot of problems?
	# - Yes
	# - Is there a better solution?
	# - Ahhhhhhhh...good enough?
	for_group: str
	for_subgroup: int
	lessons: list[Lesson]


def day_num_to_str(num: int) -> str:
	match num:
		case 0:
			return "Понедельник"
		case 1:
			return "Вторник"
		case 2:
			return "Среда"
		case 3:
			return "Четверг"
		case 4:
			return "Пятница"
		case 5:
			return "Суббота"
		case 6:
			return "Воскресенье"
		case _:
			return "(ошибка!)"
