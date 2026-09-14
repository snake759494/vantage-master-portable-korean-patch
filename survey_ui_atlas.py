# -*- coding: utf-8 -*-
"""Look at a UI atlas closely enough to write a label box for it.

``ui_texture_text`` needs three numbers per label -- x, y, w, h -- and the only
way to get them is to look.  This is the eyepiece:

    python survey_ui_atlas.py view sysmenu                  # whole atlas, 2x
    python survey_ui_atlas.py view sysmenu 0 76 130 135 6   # a region, 6x
    python survey_ui_atlas.py alpha sysmenu                 # opacity as luminance
    python survey_ui_atlas.py rows sysmenu 0 190            # ink rows in a column band
    python survey_ui_atlas.py cols sysmenu 80 95            # ink columns in a row band
    python survey_ui_atlas.py boxes sysmenu 0 74 96 256      # tight ink boxes in a region
    python survey_ui_atlas.py dump sysmenu 0 80 40 96       # raw RGBA, one row a line
    python survey_ui_atlas.py after sysmenu 0 76 130 135 6  # the same region, as patched

``view`` composites over mid grey and draws a 16px grid with coordinates, which
is what makes a box readable off the picture.  ``alpha`` throws the colour away
and shows opacity, which is how a label on a dark plate becomes legible.

"ink" here means "far from the median of the band", the same rule
``patch_ui_textures.analyse`` uses, so what this prints is what that will find.
"""

from __future__ import annotations

import argparse
import io
import statistics
from collections import Counter
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw

import falcom_itp as itp

ISO = Path("Vantage Master Portable (1.01).iso")
ISO_DIR = "/PSP_GAME/USRDIR/data/system"
RAW = Path("itp_work/raw")
OUT = Path("itp_work/preview")
SCRATCH = Path("itp_work/tex/_survey.itp")


PATCHED = Path("itp_work/patched")


def load_patched(stem: str) -> itp.ItpImage:
    """The rebuilt atlas, padded back to the length the ISO slot holds.

    The padding is NUL bytes appended to a complete stream, and the loader
    rejects trailing bytes, so the length is found by growing the slice until
    it parses.
    """
    raw = PATCHED.joinpath(f"{stem}.itp").read_bytes()
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    for size in range(len(raw.rstrip(bytes(1))), len(raw) + 1):
        SCRATCH.write_bytes(raw[:size])
        try:
            return itp.load(SCRATCH)
        except Exception:
            continue
    raise SystemExit(f"{stem}: itp_work/patched copy will not decode")


def load(stem: str) -> itp.ItpImage:
    """The atlas as it ships -- from ``itp_work/raw`` if it has been extracted."""
    local = RAW / f"{stem}.itp"
    if local.exists():
        return itp.load(local)
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


def colour(image: itp.ItpImage, x: int, y: int):
    return image.palette[image.pixels[y * image.width + x]]


def lum(rgba) -> int:
    return (rgba[0] * 299 + rgba[1] * 587 + rgba[2] * 114) // 1000


def rgba_image(image: itp.ItpImage) -> Image.Image:
    out = Image.new("RGBA", (image.width, image.height))
    out.putdata([image.palette[index] for index in image.pixels])
    return out


def gridded(view: Image.Image, x0: int, y0: int, scale: int) -> Image.Image:
    view = view.resize((view.width * scale, view.height * scale), Image.NEAREST)
    draw = ImageDraw.Draw(view)
    step = 16 if scale <= 4 else 8
    for gx in range(x0 - x0 % step + step, x0 + view.width // scale, step):
        column = (gx - x0) * scale
        draw.line([(column, 0), (column, view.height)], fill=(255, 0, 0))
        draw.text((column + 2, 1), str(gx), fill=(255, 90, 90))
    for gy in range(y0 - y0 % step + step, y0 + view.height // scale, step):
        row = (gy - y0) * scale
        draw.line([(0, row), (view.width, row)], fill=(255, 0, 0))
        draw.text((2, row + 1), str(gy), fill=(255, 90, 90))
    return view


def cmd_view(image, stem, box, scale, plate) -> Path:
    x0, y0, x1, y1 = box
    fg = rgba_image(image).crop((x0, y0, x1, y1))
    back = Image.new("RGBA", fg.size, plate)
    back.alpha_composite(fg)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"view_{stem}.png"
    gridded(back.convert("RGB"), x0, y0, scale).save(path)
    return path


def cmd_alpha(image, stem, box, scale) -> Path:
    x0, y0, x1, y1 = box
    plane = Image.new("L", (image.width, image.height))
    plane.putdata([image.palette[index][3] for index in image.pixels])
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"alpha_{stem}.png"
    gridded(plane.crop((x0, y0, x1, y1)).convert("RGB"), x0, y0, scale).save(path)
    return path


def runs(hits, floor: int, gap: int):
    out, cur = [], None
    for index, count in hits:
        if count >= floor:
            cur = [index, index] if cur is None else [cur[0], index]
        elif cur is not None:
            out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    merged = []
    for run in out:
        if merged and run[0] - merged[-1][1] <= gap:
            merged[-1][1] = run[1]
        else:
            merged.append(run)
    return [(a, b, b - a + 1) for a, b in merged]


def band_ink(image, xs, ys):
    """Pixels that stand out from the band -- by opacity or by brightness."""
    alphas = [colour(image, x, y)[3] for y in ys for x in xs]
    base_alpha = statistics.median(alphas)
    lums = [lum(colour(image, x, y)) for y in ys for x in xs]
    base_lum = statistics.median(lums)

    def ink(x, y) -> bool:
        rgba = colour(image, x, y)
        return abs(rgba[3] - base_alpha) > 40 or (
            rgba[3] > 100 and abs(lum(rgba) - base_lum) > 60
        )

    return ink


def cmd_rows(image, x0, x1, gap):
    xs = range(x0, x1)
    ink = band_ink(image, xs, range(image.height))
    hits = [(y, sum(1 for x in xs if ink(x, y))) for y in range(image.height)]
    return runs(hits, floor=2, gap=gap)


def cmd_cols(image, y0, y1, gap):
    ys = range(y0, y1 + 1)
    ink = band_ink(image, range(image.width), ys)
    hits = [(x, sum(1 for y in ys if ink(x, y))) for x in range(image.width)]
    return runs(hits, floor=1, gap=gap)


def cmd_boxes(image, box, gap: int, floor: int | None = None):
    """The tight ink box of every label in a region, ready to paste into a table.

    A label box has to be the bounding rectangle of the ink it replaces: the
    patcher reads the plate from the columns just outside it, so a box with
    slack in it picks up whatever the atlas packs alongside.  Ink here is a
    pixel far from its own row's commonest colour, which holds as long as the
    region given is wide enough for the plate to outvote the lettering.
    """
    x0, y0, x1, y1 = box
    # A stroke or two is a label; one or two stray pixels is the rounded end of
    # a plate, so a band has to carry a few percent of the width to count.
    floor = floor or max(3, (x1 - x0) // 12)
    marks = []
    for y in range(y0, y1):
        row = [colour(image, x, y) for x in range(x0, x1)]
        # A row usually crosses more than one background -- a plate and the
        # transparent atlas around it, or two bands of a gradient -- and any
        # colour with a real share of the row is one of them.  A stroke never
        # has that share, so what is left over is the lettering.
        counts = Counter(row)
        base = [c for c, n in counts.items() if n >= len(row) * 0.12] or [counts.most_common(1)[0][0]]
        marks.append([
            min(sum(abs(a - b) for a, b in zip(c, e)) for e in base) > 90 for c in row
        ])
    # Rows of one label run together and rows of two do not, so bands are cut
    # at the first empty row; columns are merged across ``gap`` so the glyphs
    # of a label come back as one box rather than one box each.
    bands = runs([(y0 + i, sum(row)) for i, row in enumerate(marks)], floor=floor, gap=1)
    out = []
    for top, bottom, _height in bands:
        columns = [
            (x0 + i, sum(1 for y in range(top, bottom + 1) if marks[y - y0][i]))
            for i in range(x1 - x0)
        ]
        for left, right, _width in runs(columns, floor=1, gap=gap):
            rows = [y for y in range(top, bottom + 1)
                    if any(marks[y - y0][x - x0] for x in range(left, right + 1))]
            out.append((left, rows[0], right - left + 1, rows[-1] - rows[0] + 1))
    return out


def cmd_dump(image, box) -> None:
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        cells = []
        for x in range(x0, x1):
            r, g, b, a = colour(image, x, y)
            cells.append(f"{r:3d},{g:3d},{b:3d},{a:3d}")
        print(f"{y:3d} " + " | ".join(cells))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",
                        choices=("view", "alpha", "after", "rows", "cols", "boxes", "dump"))
    parser.add_argument("stem")
    parser.add_argument("box", nargs="*", type=int)
    parser.add_argument("--gap", type=int, default=5, help="merge runs closer than this")
    parser.add_argument("--floor", type=int, help="boxes: ink pixels a row needs to count")
    parser.add_argument("--plate", type=int, nargs=3, default=(110, 110, 120),
                        help="the colour view/dump composites over")
    args = parser.parse_args()

    image = load_patched(args.stem) if args.mode == "after" else load(args.stem)
    if args.mode in ("view", "alpha", "after"):
        box = args.box[:4] if len(args.box) >= 4 else [0, 0, image.width, image.height]
        scale = args.box[4] if len(args.box) >= 5 else 2
        plate = (*args.plate, 255)
        if args.mode == "alpha":
            path = cmd_alpha(image, args.stem, box, scale)
        else:
            name = f"{args.stem}_after" if args.mode == "after" else args.stem
            path = cmd_view(image, name, box, scale, plate)
        print(path)
    elif args.mode == "rows":
        x0, x1 = args.box[:2]
        print(cmd_rows(image, x0, x1, args.gap))
    elif args.mode == "cols":
        y0, y1 = args.box[:2]
        print(cmd_cols(image, y0, y1, args.gap))
    elif args.mode == "boxes":
        for found in cmd_boxes(image, args.box[:4], args.gap, args.floor):
            print("    (%d, %d, %d, %d, \"\")," % found)
    else:
        cmd_dump(image, args.box[:4])


if __name__ == "__main__":
    main()
