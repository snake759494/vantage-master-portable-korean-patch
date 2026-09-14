"""Replace pre-rendered Japanese label art inside ITP textures with Korean.

The atlases are sampled by fixed UV rectangles, so a replacement has to stay
inside the box the original text occupied.  Rather than guess the blend mode
the game uses, every replacement is drawn with palette entries that the
original text in that same box already used: an alpha ramp is collected from
the box, the Korean glyphs are rasterised to a coverage mask, and the coverage
is quantised onto that ramp.  Whatever the original looked like on screen, the
replacement is drawn the same way.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from falcom_itp import ItpImage

RAMP_STEPS = 6


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


def alpha_of(image: ItpImage, index: int) -> int:
    return image.palette[index][3]


def crop_indices(image: ItpImage, box: Box) -> list[list[int]]:
    return [
        list(image.pixels[y * image.width + box.x : y * image.width + box.right])
        for y in range(box.y, box.bottom)
    ]


def find_lines(
    image: ItpImage,
    box: Box,
    threshold: int = 24,
    row_gap: int = 2,
    col_gap: int = 8,
) -> list[Box]:
    """Split a region into the text lines and runs the artist drew in it."""
    rows = crop_indices(image, box)
    ink = [[alpha_of(image, index) > threshold for index in row] for row in rows]

    bands: list[tuple[int, int]] = []
    start = None
    blank = 0
    for y, row in enumerate(ink):
        if any(row):
            if start is None:
                start = y
            blank = 0
        elif start is not None:
            blank += 1
            if blank > row_gap:
                bands.append((start, y - blank))
                start = None
    if start is not None:
        bands.append((start, len(ink) - 1))

    boxes: list[Box] = []
    for top, bottom in bands:
        columns = [
            any(ink[y][x] for y in range(top, bottom + 1)) for x in range(box.w)
        ]
        run_start = None
        gap = 0
        runs: list[tuple[int, int]] = []
        for x, filled in enumerate(columns):
            if filled:
                if run_start is None:
                    run_start = x
                gap = 0
            elif run_start is not None:
                gap += 1
                if gap > col_gap:
                    runs.append((run_start, x - gap))
                    run_start = None
        if run_start is not None:
            runs.append((run_start, box.w - 1))
        for left, right in runs:
            boxes.append(
                Box(box.x + left, box.y + top, right - left + 1, bottom - top + 1)
            )
    return boxes


def build_ramp(image: ItpImage, box: Box, steps: int = RAMP_STEPS) -> tuple[int, list[int]]:
    """Return (background index, ramp of indices ordered by rising alpha)."""
    counts: Counter[int] = Counter()
    for row in crop_indices(image, box):
        counts.update(row)
    background = min(counts, key=lambda index: (alpha_of(image, index), -counts[index]))
    candidates = sorted(counts, key=lambda index: alpha_of(image, index))
    if len(candidates) < 2:
        raise ValueError(f"box {box} has no ink to sample")

    top_alpha = alpha_of(image, candidates[-1])
    base_alpha = alpha_of(image, background)
    ramp: list[int] = []
    for step in range(1, steps + 1):
        target = base_alpha + (top_alpha - base_alpha) * step / steps
        pick = min(candidates, key=lambda index: (abs(alpha_of(image, index) - target), -counts[index]))
        ramp.append(pick)
    return background, ramp


def clear(image: ItpImage, box: Box, background: int) -> None:
    for y in range(box.y, box.bottom):
        start = y * image.width + box.x
        image.pixels[start : start + box.w] = bytes([background]) * box.w


def coverage_mask(text: str, font: ImageFont.FreeTypeFont, box: Box, align: str) -> Image.Image:
    """Rasterise ``text`` into a box-sized 8-bit coverage mask."""
    left, top, right, bottom = font.getbbox(text)
    canvas = Image.new("L", (max(right - left, 1) + 4, max(bottom - top, 1) + 4), 0)
    ImageDraw.Draw(canvas).text((2 - left, 2 - top), text, font=font, fill=255)
    canvas = canvas.crop(canvas.getbbox() or (0, 0, 1, 1))

    if canvas.width > box.w or canvas.height > box.h:
        scale = min(box.w / canvas.width, box.h / canvas.height)
        canvas = canvas.resize(
            (max(int(canvas.width * scale), 1), max(int(canvas.height * scale), 1)),
            Image.Resampling.LANCZOS,
        )

    mask = Image.new("L", (box.w, box.h), 0)
    if align == "left":
        x = 0
    elif align == "right":
        x = box.w - canvas.width
    else:
        x = (box.w - canvas.width) // 2
    mask.paste(canvas, (x, (box.h - canvas.height) // 2))
    return mask


def draw_text(
    image: ItpImage,
    box: Box,
    text: str,
    font: ImageFont.FreeTypeFont,
    align: str = "center",
    ramp: tuple[int, list[int]] | None = None,
) -> None:
    background, levels = ramp if ramp else build_ramp(image, box)
    mask = coverage_mask(text, font, box, align)
    clear(image, box, background)
    data = mask.load()
    for y in range(box.h):
        row = (box.y + y) * image.width + box.x
        for x in range(box.w):
            value = data[x, y]
            if value < 16:
                continue
            step = min(len(levels) - 1, (value * len(levels)) // 256)
            image.pixels[row + x] = levels[step]


def fit_font(text: str, path: str, box: Box, max_size: int | None = None) -> ImageFont.FreeTypeFont:
    """Largest font size whose rendering of ``text`` still fits ``box``."""
    ceiling = max_size or box.h
    for size in range(ceiling, 5, -1):
        font = ImageFont.truetype(path, size)
        left, top, right, bottom = font.getbbox(text)
        if right - left <= box.w and bottom - top <= box.h:
            return font
    return ImageFont.truetype(path, 6)
