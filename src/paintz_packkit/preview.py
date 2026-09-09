from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .svg_label import find_font

VISIBLE_CIRCUMFERENCE = 0.50


def _preview_font(size: int):
    path = find_font()
    if path:
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _visible_front(label: Image.Image) -> Image.Image:
    width, height = label.size
    crop_width = int(width * VISIBLE_CIRCUMFERENCE)
    x1 = (width - crop_width) // 2
    return label.crop((x1, 0, x1 + crop_width, height))


def save_preview(label: Image.Image, out: Path):
    canvas_width, canvas_height = 900, 1250
    canvas = Image.new("RGB", (canvas_width, canvas_height), (224, 224, 216))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((225, 1110, 675, 1185), fill=(180, 180, 172))

    body_x1, body_y1, body_x2, body_y2 = 250, 160, 650, 1080
    body_width, body_height = body_x2 - body_x1, body_y2 - body_y1
    front = _visible_front(label).resize((body_width, body_height), Image.Resampling.LANCZOS).convert("RGB")
    mask = Image.new("L", (body_width, body_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, body_width - 1, body_height - 1), radius=42, fill=255)
    canvas.paste(front, (body_x1, body_y1), mask)

    shade = Image.new("RGBA", (body_width, body_height), (0, 0, 0, 0))
    pixels = shade.load()
    for x in range(body_width):
        normalized = abs((x / max(1, body_width - 1)) * 2.0 - 1.0)
        alpha = int(90 * (normalized ** 2.3))
        for y in range(body_height):
            pixels[x, y] = (0, 0, 0, alpha)
    rgba = canvas.convert("RGBA")
    rgba.alpha_composite(shade, (body_x1, body_y1))
    canvas = rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((body_x1, body_y1, body_x2, body_y2), radius=42, outline=(34, 34, 31), width=5)
    draw.line((body_x1 + 12, body_y2 - 20, body_x2 - 12, body_y2 - 20), fill=(38, 38, 35), width=6)
    draw.rectangle((278, 115, 622, 205), fill=(68, 69, 64), outline=(30, 30, 29), width=4)
    draw.ellipse((278, 95, 622, 150), fill=(105, 106, 101), outline=(35, 35, 32), width=4)
    draw.rounded_rectangle((365, 45, 535, 125), radius=20, fill=(25, 25, 24), outline=(15, 15, 15), width=3)
    canvas.save(out)


def save_preview_catalog(items: list[tuple[dict, str, Path]], out: Path, columns: int = 4):
    if not items:
        return
    thumb_width, thumb_height = 360, 500
    cell_width, cell_height = 420, 610
    margin_x, margin_y, header_height = 50, 42, 145
    rows = (len(items) + columns - 1) // columns
    width = margin_x * 2 + columns * cell_width
    height = header_height + margin_y + rows * cell_height + margin_y
    canvas = Image.new("RGB", (width, height), (232, 232, 224))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin_x, 28), "PaintZ PackKit", font=_preview_font(52), fill=(29, 31, 27))
    draw.text((margin_x, 88), "Generated paint catalogue", font=_preview_font(27), fill=(83, 82, 55))

    for index, (paint, code, preview_path) in enumerate(items):
        column, row = index % columns, index // columns
        x0 = margin_x + column * cell_width
        y0 = header_height + margin_y + row * cell_height
        with Image.open(preview_path) as image:
            image = image.convert("RGB")
            image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            canvas.paste(image, (x0 + (cell_width - image.width) // 2, y0))
        for text, y, size, fill in [
            (str(paint["name"]).upper(), y0 + 505, 27, (29, 31, 27)),
            (code, y0 + 548, 20, (83, 82, 55)),
        ]:
            font = _preview_font(size)
            box = draw.textbbox((0, 0), text, font=font)
            draw.text((x0 + cell_width / 2 - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)
    canvas.save(out)
