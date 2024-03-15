from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def count_lines(text: str) -> int:
    n = text.count("\n")
    return n


def generate(text: str, today: bool):
    text = "\n" + text
    lines = count_lines(text)
    if today:
        image = Image.new("RGB", (500, lines * 30), (255, 255, 255))
    else:
        image = Image.new("RGB", (500, lines * 19), (255, 255, 255))

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 15)
    draw.text((10, 10), text, font=font, fill=(0, 0, 0))

    img_byte_arr = BytesIO()
    img_byte_arr.name = "generated_image.jpeg"
    image.save(img_byte_arr, "JPEG")
    img_byte_arr.seek(0)
    return img_byte_arr
