from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


KANJI_OFFSET = 0x1CEC4
TILE_BYTES = 64


def raw_tile(source: bytes, index: int) -> Image.Image:
    raw = source[KANJI_OFFSET + index * TILE_BYTES : KANJI_OFFSET + (index + 1) * TILE_BYTES]
    values = []
    for y in range(16):
        for value in raw[y * 4 : y * 4 + 4]:
            values.extend((value & 3, (value >> 2) & 3, (value >> 4) & 3, (value >> 6) & 3))
    image = Image.new("L", (16, 16), 0)
    image.putdata([0 if value == 0 else 255 for value in values])
    return image


def score(screen: np.ndarray, template: np.ndarray, x: int, y: int) -> tuple[float, float, int]:
    view = screen[y : y + template.shape[0], x : x + template.shape[1]]
    if view.shape != template.shape:
        return (-1.0, -1.0, 0)
    inter = int(np.logical_and(view, template).sum())
    tcount = int(template.sum())
    vcount = int(view.sum())
    if not tcount or not vcount:
        return (-1.0, -1.0, inter)
    precision = inter / vcount
    recall = inter / tcount
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return (f1, recall, inter)


def main() -> None:
    source = Path("pspfont.dat").read_bytes()
    screenshot = np.asarray(Image.open(Path("D:/psp/ppsspp_win/memstick/PSP/SCREENSHOT/ULJM05332_00008.jpg")).convert("RGB"))
    # Text is near-white and nearly neutral; the dark/blue dialog background is excluded.
    screen = (screenshot.min(axis=2) > 155) & ((screenshot.max(axis=2) - screenshot.min(axis=2)) < 70)
    base = raw_tile(source, 2567)
    transforms = {
        "none": base,
        "rot90": base.rotate(90, expand=False),
        "rot180": base.rotate(180, expand=False),
        "rot270": base.rotate(270, expand=False),
        "flip_x": base.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        "flip_y": base.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        "transpose": base.transpose(Image.Transpose.TRANSPOSE),
        "transverse": base.transpose(Image.Transpose.TRANSVERSE),
    }
    for name, tile in transforms.items():
        template = np.asarray(tile.resize((32, 32), Image.Resampling.NEAREST)) > 0
        best = (-1.0, -1.0, 0, 0, 0)
        for y in range(50, 160 - 32):
            for x in range(440, 940 - 32):
                f1, recall, inter = score(screen, template, x, y)
                if (f1, recall) > (best[0], best[1]):
                    best = (f1, recall, inter, x, y)
        print(name, best, "template_pixels", int(template.sum()))


if __name__ == "__main__":
    main()
