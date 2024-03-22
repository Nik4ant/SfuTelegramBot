import os
import logging
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .common import *


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


# region   -- Drawing
def _draw_at(drawer: ImageDraw, text: str, font: ImageFont, horizontal_offset: int, vertical_offset: int, color) -> tuple[int, int]:
	"""
	@return: Additional offset based on text size
	"""
	# FIXME: textwrap works, but font.getbbox ignores the '\n'
	# formated_text: str = '\n'.join(textwrap.wrap(text, width=32))

	# (left, top, right, bottom) bounding box
	text_bbox: tuple[int, int, int, int] = font.getbbox(text)

	drawer.multiline_text(
		(horizontal_offset, vertical_offset),
		text, fill=color, anchor="ls", font=font
	)
	return abs(text_bbox[0] - text_bbox[2]), abs(text_bbox[1] - text_bbox[3])


def _gen_day(day: list[Lesson], day_num: int, file_path: str, dark_theme: bool) -> None:
	"""Generates img for specified day at specified path"""
	schema: dict[str, str] = COLOR_SCHEMA["dark"] if dark_theme else COLOR_SCHEMA["light"]
	day_font = ImageFont.truetype(FONT_PATH, 24)
	title_font = ImageFont.truetype(FONT_PATH, 18)
	default_font = ImageFont.truetype(FONT_PATH, 14)

	height: int = round((BASE_HEIGHT + OFFSET_BETWEEN_LESSONS + OFFSET_BETWEEN_ROWS * EXPECTED_ROWS_PER_LESSON) * 1.5 * len(day))
	im = Image.new(
		"RGB",
		# ...Good enough...
		(1080, height),
		schema["bg"]
	)
	dr = ImageDraw.Draw(im)

	v_offset: int = BASE_HEIGHT
	h_offset: int = BASE_WIDTH
	# Day name (row -1)
	v_offset += _draw_at(dr, day_num_to_str(day_num), day_font, h_offset, v_offset,
						schema["primary"])[1]
	
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
		v_offset += _draw_at(dr, lesson.sync_status, default_font, h_offset + BASE_WIDTH * 2,
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


def generate_day(day: Day, dark_theme: bool = True) -> str:
	"""Returns path to the generated image for given day"""
	# Нет пар или воскресенье
	if day.day_num == 6 or len(day.lessons) == 0:
		return PLACEHOLDER_IMG_DARK if dark_theme else PLACEHOLDER_IMG_LIGHT
	
	light_theme_img: str = _file_path_for(day.for_group, day.for_subgroup, day.week_num, day.day_num, False)
	dark_theme_img: str = _file_path_for(day.for_group, day.for_subgroup, day.week_num, day.day_num, True)
	# Generate both dark and light theme variants
	_gen_day(day.lessons, day.day_num, light_theme_img, False)
	_gen_day(day.lessons, day.day_num, dark_theme_img, True)
	# However can't return path to both variants!
	return dark_theme_img if dark_theme else light_theme_img
# endregion


# region   -- API
def get_day_image(group: str, subgroup: str, week_num: int, day_index: int, dark_theme: bool = True) -> str:
	path: str = _file_path_for(group, subgroup, week_num, day_index, dark_theme)
	if os.path.isfile(path):
		return path

	return PLACEHOLDER_IMG_DARK if dark_theme else PLACEHOLDER_IMG_LIGHT


def get_week_images(group: str, subgroup: str, week_num: int, dark_theme: bool = True) -> list[str]:
	return [get_day_image(group, subgroup, week_num, i, dark_theme) for i in range(6)]
# endregion


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
