import os
import logging
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .parser import Lesson, LessonType, EVEN_DAY_NUM, ODD_DAY_NUM
from sfu_api.timetable import Lesson, LessonType


IMG_DIR_ROOT: str = os.path.join(os.getcwd(), "_timetable_images")
IMG_OUTPUT_DIR: str = os.path.join(IMG_DIR_ROOT, "_output")
IMG_ASSETS_DIR: str = os.path.join(IMG_DIR_ROOT, "_assets")
COLOR_SCHEMA = {
	"dark": {
		"text": "#e5ecf0",
		"bg": "#0b1014",
		"primary": "#a6bfce",
		"secondary": "#373a67",
		"accent": "#8277b6"
	},
	"light": {
		"text": "#0f161a",
		"bg": "#ebf0f4",
		"primary": "#314a59",
		"secondary": "#989bc8",
		"accent": "#534988"
	}
}
LESSON_TYPE_COLORS = {
	LessonType.LECTURE: "#ff6000",
	LessonType.PRACTISE: "#22B957",
	LessonType.LAB: "#d01eb2"
}
FONT_PATH: str = os.path.join(IMG_ASSETS_DIR, "Roboto-Medium.ttf")
PLACEHOLDER_IMG_LIGHT: str = os.path.join(IMG_ASSETS_DIR, "default_img_light.png")
PLACEHOLDER_IMG_DARK: str = os.path.join(IMG_ASSETS_DIR, "default_img_dark.png")
BASE_HEIGHT: int = 32
BASE_WIDTH: int = 5
OFFSET_BETWEEN_LESSONS: int = 24
# Offset between lesson's "parts" (rows): name, time, location, teacher, etc.
OFFSET_BETWEEN_ROWS: int = 10
EXPECTED_ROWS_PER_LESSON: int = 5


def _draw_at(drawer: ImageDraw, text: str, font: ImageFont, horizontal_offset: int, vertical_offset: int, color) -> tuple[int, int]:
	"""
	@return: Additional offset based on text size
	"""
	formated_text: str = textwrap.wrap(text, width=32)
	# (left, top, right, bottom) bounding box
	text_bbox: tuple[int, int, int, int] = font.getbbox(formated_text)
	
	drawer.multiline_text(
		(horizontal_offset, vertical_offset),
		formated_text, fill=color, anchor="ls", font=font
	)
	return abs(text_bbox[0] - text_bbox[2]), abs(text_bbox[1] - text_bbox[3])


def _gen_day(day: list[Lesson], file_path: str, dark_theme: bool = False) -> None:
	"""Generates img for specified day at specified path"""
	schema: dict[str, str] = COLOR_SCHEMA["dark"] if dark_theme else COLOR_SCHEMA["light"]
	title_font = ImageFont.truetype(FONT_PATH, 18)
	default_font = ImageFont.truetype(FONT_PATH, 14)

	im = Image.new(
		"RGB",
		# TODO: calculate size automatically and crop later
		(740, 500),
		schema["bg"]
	)
	print("DEBUG: ", im.size)
	dr = ImageDraw.Draw(im)

	v_offset: int = BASE_HEIGHT
	h_offset: int = BASE_WIDTH
	for i, lesson in enumerate(day, start=1):
		lesson: Lesson

		# Title (row 0)
		v_offset += _draw_at(dr, lesson.name, title_font, h_offset, v_offset,
							 schema["text"])[1]
		# Lesson type (row 1)
		_row_1_offset = _draw_at(dr, lesson.class_type, default_font, h_offset,
								 v_offset, LESSON_TYPE_COLORS[lesson.class_type])
		h_offset += _row_1_offset[0]
		# Sync or async (row 1)
		sync_or_async: str = "Синхронно" if lesson.is_sync else "Асинхронно"
		v_offset += _draw_at(dr, sync_or_async, default_font, h_offset + BASE_WIDTH * 2,
							v_offset, schema["text"])[1] + OFFSET_BETWEEN_ROWS
		h_offset -= _row_1_offset[0]
		# Duration (row 2)
		v_offset += _draw_at(dr, lesson.duration_time, default_font, h_offset,
							 v_offset, schema["text"])[1] + OFFSET_BETWEEN_ROWS
		# Location (row 3)
		v_offset += _draw_at(dr, lesson.full_location, default_font, h_offset,
							 v_offset, schema["text"])[1] + OFFSET_BETWEEN_ROWS
		# Teacher (row 4)
		v_offset += _draw_at(dr, lesson.teacher, default_font, h_offset,
							 v_offset, schema["text"])[1] + OFFSET_BETWEEN_ROWS

		v_offset += OFFSET_BETWEEN_LESSONS

	im.save(file_path)


def generate_all_day(group: str, subgroup: str, week_num: int, day_index: int, data: list[Lesson]) -> None:
	"""Generates all timetable variations for specified day (light/dark themes)"""
	# Нет пар или воскресенье
	if len(data) == 0 or day_index == 6:
		return

	_gen_day(data, _file_path_for(group, subgroup, week_num, day_index, False), False)
	_gen_day(data, _file_path_for(group, subgroup, week_num, day_index, True), True)


def try_get_day(group: str, subgroup: str, week_num: int, day_index: int, dark_theme: bool = True) -> str:
	path: str = _file_path_for(group, subgroup, week_num, day_index, dark_theme)
	if os.path.isfile(path):
		return path

	return PLACEHOLDER_IMG_DARK if dark_theme else PLACEHOLDER_IMG_LIGHT


def try_get_week(group: str, subgroup: str, week_num: int, dark_theme: bool = True) -> list[str]:
	return [try_get_day(group, subgroup, week_num, i, dark_theme) for i in range(6)]


def _file_path_for(group: str, subgroup: str, week_num: int, day_index: int, dark_theme: bool) -> str:
	return os.path.join(
		IMG_OUTPUT_DIR, f"{group}_{subgroup}_{day_index}_{week_num}"
	) + ("dark" if dark_theme else "light") + ".png"


def init() -> None:
	logging.info(f"Path to generator assets: {IMG_ASSETS_DIR}")
	logging.info(f"Path to generator output: {IMG_OUTPUT_DIR}")
	os.makedirs(IMG_DIR_ROOT, exist_ok=True)
	os.makedirs(IMG_ASSETS_DIR, exist_ok=True)
	os.makedirs(IMG_OUTPUT_DIR, exist_ok=True)


def delete_all() -> None:
	"""Deletes all generated images"""
	for file in os.listdir(IMG_OUTPUT_DIR):
		os.remove(os.path.join(IMG_OUTPUT_DIR, file))
