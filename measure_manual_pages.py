# -*- coding: utf-8 -*-
"""Measure a rulebook page so its lines can be written into ``manual_text``.

Three things have to be known before a line can be replaced: which rows the
Japanese occupies, which columns it reaches, and -- for a table -- where the
cell it lives in ends.  This prints all three.

    python measure_manual_pages.py rows histor2            # row bands
    python measure_manual_pages.py rows manual2 --x 112 300 # ... in one column
    python measure_manual_pages.py cols manual14 117 147   # column runs in a band
    python measure_manual_pages.py ruler manual2           # a 2x render with a ruler
    python measure_manual_pages.py sheet histor8 histor9 .. # built pages, four to a sheet

``rows`` uses two detectors and prints both, because neither works everywhere.
"contrast" calls a pixel ink when it is far from its own row's background,
which is right for a page of plain parchment and useless once an illustration
fills the row.  "outline" looks for a bright core with a dark rim two pixels
away, which is what the white captions over the night-sky art are and what
smooth artwork almost never is.
"""

from __future__ import annotations

import argparse
import io
import statistics
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw

import falcom_itp as itp

ISO = Path("Vantage Master Portable (1.01).iso")
ISO_DIR = "/PSP_GAME/USRDIR/data/system"
SCRATCH = Path("itp_work/tex/_measure.itp")
OUT = Path("itp_work/preview")

TEXT_LEFT, TEXT_RIGHT = 112, 472
TOP, BOTTOM = 12, 264


def load(stem: str) -> itp.ItpImage:
    with ISO.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, iso_path=f"{ISO_DIR}/{stem}.itp")
        finally:
            iso.close()
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    SCRATCH.write_bytes(buffer.getvalue())
    return itp.load(SCRATCH)


def lum(image: itp.ItpImage, x: int, y: int) -> int:
    colour = image.palette[image.pixels[y * image.width + x]]
    return (colour[0] * 299 + colour[1] * 587 + colour[2] * 114) // 1000


def runs(hits, floor: int, least: int) -> list[tuple[int, int]]:
    out, cur = [], None
    for index, count in hits:
        if count >= floor:
            cur = [index, index] if cur is None else [cur[0], index]
        elif cur is not None:
            if cur[1] - cur[0] + 1 >= least:
                out.append((cur[0], cur[1]))
            cur = None
    if cur and cur[1] - cur[0] + 1 >= least:
        out.append((cur[0], cur[1]))
    return out


def rows_by_contrast(image, x0, x1) -> list[tuple[int, int]]:
    hits = []
    for y in range(TOP, BOTTOM):
        row = [lum(image, x, y) for x in range(x0, x1)]
        base = statistics.median(row)
        hits.append((y, sum(1 for v in row if abs(v - base) > 60)))
    return runs(hits, floor=8, least=4)


def rows_by_outline(image, x0, x1) -> list[tuple[int, int]]:
    hits = []
    for y in range(TOP, BOTTOM):
        count = 0
        for x in range(x0, x1):
            if lum(image, x, y) > 215 and min(
                lum(image, max(0, x - 2), y), lum(image, min(image.width - 1, x + 2), y)
            ) < 90:
                count += 1
        hits.append((y, count))
    return runs(hits, floor=5, least=4)


def cols(image, y0, y1) -> list[tuple[int, int, int]]:
    base = statistics.median(
        [lum(image, x, y) for y in range(y0, y1 + 1) for x in range(TEXT_LEFT, TEXT_RIGHT)]
    )
    hits = []
    for x in range(TEXT_LEFT - 4, TEXT_RIGHT + 8):
        hits.append((x, sum(1 for y in range(y0, y1 + 1)
                            if abs(lum(image, x, y) - base) > 55)))
    merged = []
    for left, right in runs(hits, floor=2, least=1):
        if merged and left - merged[-1][1] <= 8:
            merged[-1][1] = right
        else:
            merged.append([left, right])
    return [(a, b, b - a + 1) for a, b in merged]


PATCHED = Path("itp_work/patched")


def load_patched(stem: str) -> itp.ItpImage:
    """A rebuilt page, unpadded.  It is NUL-padded to the ISO slot length, and
    the loader rejects trailing bytes, so grow the slice until it parses."""
    raw = PATCHED.joinpath(f"{stem}.itp").read_bytes()
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    for size in range(len(raw.rstrip(bytes(1))), len(raw) + 1):
        SCRATCH.write_bytes(raw[:size])
        try:
            return itp.load(SCRATCH)
        except Exception:
            continue
    raise SystemExit(f"{stem}: itp_work/patched copy will not decode")


def page(image: itp.ItpImage) -> Image.Image:
    fg = Image.new("RGBA", (image.width, image.height))
    fg.putdata([image.palette[index] for index in image.pixels])
    out = Image.new("RGBA", fg.size, (255, 255, 255, 255))
    out.alpha_composite(fg)
    return out.convert("RGB").crop((96, 0, 496, 270))


def sheet(stems: list[str]) -> Path:
    """Four built pages to a sheet -- enough to spot a band that missed."""
    tiles = []
    for stem in stems:
        view = page(load_patched(stem))
        pad = Image.new("RGB", (view.width, view.height + 14), (20, 20, 24))
        pad.paste(view, (0, 14))
        ImageDraw.Draw(pad).text((4, 2), stem, fill=(255, 220, 90))
        tiles.append(pad)
    columns = 2 if len(tiles) > 1 else 1
    rows = (len(tiles) + columns - 1) // columns
    out = Image.new("RGB", (tiles[0].width * columns, tiles[0].height * rows), (20, 20, 24))
    for index, tile in enumerate(tiles):
        out.paste(tile, ((index % columns) * tile.width, (index // columns) * tile.height))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "pagesheet.png"
    out.save(path)
    return path


def ruler(stem: str) -> Path:
    image = load(stem)
    fg = Image.new("RGBA", (image.width, image.height))
    fg.putdata([image.palette[index] for index in image.pixels])
    page = Image.new("RGBA", fg.size, (255, 255, 255, 255))
    page.alpha_composite(fg)
    view = page.convert("RGB").crop((96, 0, 496, 300))
    view = view.resize((view.width * 2, view.height * 2), Image.NEAREST)
    draw = ImageDraw.Draw(view)
    for y in range(8, 300, 8):
        major = y % 32 == 0
        draw.line([(0, y * 2), (view.width if major else 26, y * 2)],
                  fill=(255, 0, 0) if major else (0, 190, 255))
        draw.text((28, y * 2 - 5), str(y),
                  fill=(255, 60, 60) if major else (0, 160, 230))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"ruler_{stem}.png"
    view.save(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("rows", "cols", "ruler", "sheet"))
    parser.add_argument("stem", nargs="+")
    parser.add_argument("band", nargs="*", type=int, help="cols: the row band")
    parser.add_argument("--x", nargs=2, type=int, default=(TEXT_LEFT, TEXT_RIGHT))
    args = parser.parse_args()

    if args.mode == "sheet":
        print(sheet(args.stem))
        return
    stem = args.stem[0]
    if args.mode == "ruler":
        print(ruler(stem))
        return
    image = load(stem)
    if args.mode == "cols":
        y0, y1 = args.band
        print(cols(image, y0, y1))
        return
    print("contrast:", rows_by_contrast(image, *args.x))
    print("outline: ", rows_by_outline(image, *args.x))


if __name__ == "__main__":
    main()
