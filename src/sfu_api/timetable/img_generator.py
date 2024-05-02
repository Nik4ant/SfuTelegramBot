import os
import logging
import textwrap

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageType

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
# Base/Initial vertical offset
BASE_HEIGHT: int = 32
# Base/Initial horizontal offset
BASE_WIDTH: int = 5
# Max length for text (in columns) before wrapping (see textwrap.wrap)
MAX_WIDTH_COLUMNS: int = 48
OFFSET_BETWEEN_LESSONS: int = 24
# Offset between lesson's "parts" (rows): name, time, location, teacher, etc.
OFFSET_BETWEEN_ROWS: int = 10
EXPECTED_ROWS_PER_LESSON: int = 5


# region   -- Drawing
def _concat_images(images_paths: list[str], dark_theme: bool) -> ImageType:
	images: list[ImageType] = [Image.open(path) for path in images_paths]
	# region Size
	max_width = 0
	total_height = 0
	for image in images:
		image: ImageType
		total_height += image.height
		if image.width > max_width:
			max_width = image.width
	# endregion

	bg_color: str = (COLOR_SCHEMA["dark"] if dark_theme else COLOR_SCHEMA["light"])["bg"]
	target: ImageType = Image.new("RGB", (max_width, total_height), bg_color)

	v_offset: int = 0
	for i in range(len(images)):
		target.paste(images[i], (0, v_offset))
		v_offset += images[i].height

	return target


def _draw_at(drawer: ImageDraw, text: str, font: ImageFont, horizontal_offset: int, vertical_offset: int, color) -> tuple[int, int]:
	"""
	@return: Additional offset based on text size
	"""
	_lines: list[str] = textwrap.wrap(text, width=MAX_WIDTH_COLUMNS)
	formatted_text: str = '\n'.join(_lines)
	# (left, top, right, bottom) bounding box
	text_bbox: tuple[int, int, int, int] = font.getbbox(formatted_text)

	drawer.multiline_text(
		(horizontal_offset, vertical_offset),
		formatted_text, fill=color, anchor="ls", font=font
	)
	# Account for text wrapping
	new_vertical = len(_lines) * abs(text_bbox[1] - text_bbox[3])
	return abs(text_bbox[0] - text_bbox[2]), new_vertical


def _gen_day(day: list[Lesson], day_num: int, file_path: str, dark_theme: bool) -> None:
	"""Generates img for specified day at specified path"""
	schema: dict[str, str] = COLOR_SCHEMA["dark"] if dark_theme else COLOR_SCHEMA["light"]
	day_font = ImageFont.truetype(FONT_PATH, 24)
	title_font = ImageFont.truetype(FONT_PATH, 18)
	default_font = ImageFont.truetype(FONT_PATH, 14)

	height: int = round((BASE_HEIGHT + OFFSET_BETWEEN_LESSONS + OFFSET_BETWEEN_ROWS * EXPECTED_ROWS_PER_LESSON) * 1.5 * len(day))
	im = Image.new(
		"RGB",
		# Width can be a constant value thanks to text wrapping
		(16 * MAX_WIDTH_COLUMNS, height),
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
	
	light_theme_img: str = _filename_for_day(day.for_group, day.for_subgroup, day.week_num, day.day_num, False)
	dark_theme_img: str = _filename_for_day(day.for_group, day.for_subgroup, day.week_num, day.day_num, True)
	# Generate both dark and light theme variants
	_gen_day(day.lessons, day.day_num, light_theme_img, False)
	_gen_day(day.lessons, day.day_num, dark_theme_img, True)
	# However can't return path to both variants!
	return dark_theme_img if dark_theme else light_theme_img


def generate_week(days: list[Day], dark_theme: bool = True) -> str:
	images: list[str] = [generate_day(day, dark_theme) for day in days]

	path: str = _filename_for_week(days[0].for_group, days[0].for_subgroup, days[0].week_num, dark_theme)
	week_image: ImageType = _concat_images(images, dark_theme)
	week_image.save(path)
	return path
# endregion


# region   -- API
def get_day_image(group: str, subgroup: str, week_num: int, day_index: int, dark_theme: bool = True) -> str:
	path: str = _filename_for_day(group, subgroup, week_num, day_index, dark_theme)
	if os.path.isfile(path):
		return path

	return PLACEHOLDER_IMG_DARK if dark_theme else PLACEHOLDER_IMG_LIGHT


def get_week_images(group: str, subgroup: str, week_num: int, dark_theme: bool = True) -> list[str]:
	return [get_day_image(group, subgroup, week_num, i, dark_theme) for i in range(6)]
# endregion


def _filename_for_day(group: str, subgroup: str, week_num: int, day_index: int, dark_theme: bool) -> str:
	return os.path.join(
		IMG_OUTPUT_DIR, f"DAY_{group}_{subgroup}_{day_index}_{week_num}_"
	) + ("dark" if dark_theme else "light") + ".png"


def _filename_for_week(group: str, subgroup: str, week_num: int, dark_theme: bool) -> str:
	return os.path.join(
		IMG_OUTPUT_DIR, f"WEEK_{group}_{subgroup}_{week_num}_"
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
