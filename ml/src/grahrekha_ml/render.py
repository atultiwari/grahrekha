"""Render QuickDraw stroke data to images (negatives for the palm quality gate)."""

from PIL import Image, ImageDraw

Strokes = list[list[list[int]]]  # [[xs, ys], ...] in a 0-255 box


def render_quickdraw(strokes: Strokes, size: int = 256, line_width: int = 3) -> Image.Image:
    image = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(image)
    scale = (size - 1) / 255
    for xs, ys in strokes:
        points = [(x * scale, y * scale) for x, y in zip(xs, ys, strict=True)]
        if len(points) > 1:
            draw.line(points, fill=0, width=line_width)
    return image
