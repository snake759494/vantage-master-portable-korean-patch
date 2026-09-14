# -*- coding: utf-8 -*-
"""Check every rebuilt rulebook page for Japanese the repair left behind.

Eyeballing sixty-seven pages misses things, and the two ways a line can go wrong
are both measurable against the page as it shipped:

  LEFTOVER -- ink outside the Korean.  The Korean is drawn in the same colour as
              the Japanese it replaces, so "unchanged ink" catches every place
              the two happen to overlap and says nothing.  What does say
              something is ink in the part of the cleared region the Korean does
              not cover: a Korean line is shorter than the Japanese almost
              always, and anything still inked out past its end, or in a row it
              does not reach, is Japanese that got away.

  MISCOLOUR -- the repair painted the background a colour the page does not use
              there.  The cleared region should come back close to the band's
              own plate; a fill far from it is the "dark block" failure, where
              the ramp anchored on a table rule instead of the cell.

Both are reported per line with the coordinates, so a hit points straight at the
entry in ``manual_text`` that needs its band or window fixed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import ImageFont

import falcom_itp as itp
import manual_text
import patch_manual_textures as manual

ISO = Path("Vantage Master Portable (1.01).iso")
PATCHED = Path("itp_work/patched")
SCRATCH = Path("itp_work/tex/_check.itp")

# Thresholds are set to catch the failures that are visible on screen -- a whole
# surviving line, a cell painted the colour of its own rule -- and to stay quiet
# about the tens of pixels that a textured parchment and a two-pixel error in
# the estimated width of a drawn line will always produce.
LEFTOVER_PIXELS = 60
MISCOLOUR_GAP = 45
MISCOLOUR_AREA = 300
MISCOLOUR_SHARE = 0.7


def load_patched(stem: str) -> itp.ItpImage:
    raw = PATCHED.joinpath(f"{stem}.itp").read_bytes()
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    for size in range(len(raw.rstrip(bytes(1))), len(raw) + 1):
        SCRATCH.write_bytes(raw[:size])
        try:
            return itp.load(SCRATCH)
        except Exception:
            continue
    raise SystemExit(f"{stem}: itp_work/patched copy will not decode")


def line_regions(image: itp.ItpImage, lines):
    """The rows and columns each line owns, the way ``apply`` works them out."""
    fonts: dict[tuple[bool, int], ImageFont.FreeTypeFont] = {}

    def font_for(bold: bool, size: int):
        key = (bold, size)
        if key not in fonts:
            face = manual.FONT_BOLD if bold else manual.FONT_PATH
            fonts[key] = ImageFont.truetype(str(face), size)
        return fonts[key]

    out = []
    for line in lines:
        band = tuple(line["y"])
        window = tuple(line["x"]) if line.get("x") else None
        left, right = manual.ink_span(image, band, window)
        size = line.get("size", manual.FONT_SIZE)
        while True:
            font = font_for(line.get("bold", False), size)
            box = manual.line_box(line["text"], font)
            if box[3] - box[1] <= band[1] - band[0] + 3 or size <= 9:
                break
            size -= 1
        height = box[3] - box[1]
        rows = (max(1, band[0] - 1),
                min(image.height - 2, max(band[1], band[0] + height - 1) + 1))
        plate, base = manual.band_plate(image, band, left, right)
        # Where the Korean actually lands, mirroring ``apply``: the ink starts
        # at the left edge of the window (or is pushed right when aligned) and
        # its top sits on the first row of the band.
        width = int(round(sum(font.getlength(text) for _key, text in line["text"])))
        x = left
        if line.get("align") == "right":
            x = max(left, right - width - 2)
        elif line.get("align") == "center":
            lo, hi = window if window else (left, right)
            x = lo + max(0, (hi - lo - width) // 2)
        drawn = (x, band[0], x + width, band[0] + height)
        out.append({"line": line, "band": band, "rows": rows, "drawn": drawn,
                    "left": left, "right": right, "plate": plate, "base": base})
    return out


def check(stem: str, lines) -> list[str]:
    before = manual.read_texture(ISO, stem, SCRATCH)
    after = load_patched(stem)
    problems = []
    for region in line_regions(before, lines):
        top, bottom = region["rows"]
        left, right = region["left"], region["right"]
        plate = region["plate"]
        if plate is None:
            continue
        base = region["base"]
        dx0, dy0, dx1, dy1 = region["drawn"]
        # A column that is inked well above and below the band is the page frame
        # or a table rule standing on end, not a glyph.  The ramp reproduces
        # those correctly -- each is vertically uniform -- so they are not
        # leftovers and counting them flags every line on every page.
        structural = set()
        for x in range(left, right):
            probe = [y for y in (top - 6, top - 4, bottom + 4, bottom + 6)
                     if 0 <= y < after.height]
            if probe and all(
                abs(manual.lum(after.palette[after.pixels[y * after.width + x]]) - base) > 60
                for y in probe
            ):
                structural.add(x)
        leftover = far = area = 0
        for y in range(top, bottom + 1):
            row = y * before.width
            for x in range(left, right):
                new = after.palette[after.pixels[row + x]]
                if x in structural:
                    continue
                if abs(manual.lum(new) - base) > MISCOLOUR_GAP:
                    far += 1
                area += 1
                # Skip the box the Korean occupies, with a margin for its rim.
                if dx0 - 2 <= x <= dx1 + 2 and dy0 - 2 <= y <= dy1 + 2:
                    continue
                if abs(manual.lum(new) - base) > 60:
                    leftover += 1
        area = max(1, area)
        words = "".join(text for _key, text in region["line"]["text"])[:22]
        where = f"y={region['band']} x=({left},{right})"
        if leftover >= LEFTOVER_PIXELS:
            problems.append(f"LEFTOVER {leftover:4d}px  {where}  {words}")
        # Korean ink is far from the plate too, so only a region that is mostly
        # far from it has actually been painted the wrong colour.
        if area >= MISCOLOUR_AREA and far > area * MISCOLOUR_SHARE:
            problems.append(f"MISCOLOUR {far}/{area}  {where}  {words}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="*", help="default: every page")
    args = parser.parse_args()

    pages = args.pages or sorted(manual_text.PAGES)
    bad = 0
    for stem in pages:
        problems = check(stem, manual_text.PAGES[stem])
        if problems:
            bad += 1
            print(f"== {stem}")
            for problem in problems:
                print(f"   {problem}")
    print(f"{len(pages) - bad}/{len(pages)} pages clean")


if __name__ == "__main__":
    main()
