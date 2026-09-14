# -*- coding: utf-8 -*-
"""Draw the Korean rulebook text into ``data/system/manual*.itp`` and ``histor*.itp``.

These pages are 512x512 revision-1004 atlases with the whole page baked in: a
title bar, a page counter and up to a dozen lines of prose.  Nothing in the ISO
carries the words -- they exist only as pixels -- so the Japanese was read off
the page and the Korean lives in ``manual_text.py``.

Two things make them harder than the gallery pages.  The polarity flips: most
pages are dark ink on parchment, but the ones with a night-sky illustration are
white ink on dark art, so "ink" has to mean "far from this row's own
background" rather than "bright".  And a line is not one colour: the body is
brown or white, key terms are red, and cross references are blue, so each line
is drawn span by span with a colour picked out of the page's own palette.

Clearing a line works the way it does for the gallery: the background under
11px of kanji is simply gone, so each column is repainted as a ramp between the
clean rows above and the clean rows below.  The repair stops at the last column
the Japanese reached, which keeps the illustration beside a short line
untouched.
"""

from __future__ import annotations

import io
import statistics
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw, ImageFont

import falcom_itp as itp

ISO_DIR = "/PSP_GAME/USRDIR/data/system"

# The page frame runs from x=104 to x=488; the text never leaves this band.
TEXT_LEFT = 108
TEXT_RIGHT = 470

FONT_PATH = Path("NanumSquareNeo-bRg.ttf")
FONT_BOLD = Path("NanumSquareNeo-cBd.ttf")
FONT_SIZE = 12

# The Korean face has no CJK angle brackets, and a missing glyph draws as a
# box; the fullwidth parentheses read the same and are in the font.
SUBSTITUTE = {"・": "·", "－": "-", "―": "—", "〈": "（", "〉": "）"}


def lum(colour) -> int:
    return (colour[0] * 299 + colour[1] * 587 + colour[2] * 114) // 1000


def read_texture(iso_path: Path, stem: str, scratch: Path) -> itp.ItpImage:
    with iso_path.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, iso_path=f"{ISO_DIR}/{stem}.itp")
        finally:
            iso.close()
    scratch.write_bytes(buffer.getvalue())
    return itp.load(scratch)


def to_image(image: itp.ItpImage) -> Image.Image:
    out = Image.new("RGBA", (image.width, image.height))
    out.putdata([image.palette[index] for index in image.pixels])
    return out


def row_background(image: itp.ItpImage, y: int, window=None) -> int:
    lo, hi = window or (TEXT_LEFT, TEXT_RIGHT)
    row = [
        lum(image.palette[image.pixels[y * image.width + x]])
        for x in range(lo, hi)
    ]
    return int(statistics.median(row))


def is_ink(image: itp.ItpImage, x: int, y: int, base: int, gap: int = 60) -> bool:
    return abs(lum(image.palette[image.pixels[y * image.width + x]]) - base) > gap


def ink_span(image: itp.ItpImage, band, window=None) -> tuple[int, int]:
    """The first and last column the baked line reaches, inside ``window``."""
    top, bottom = band
    lo, hi = window or (TEXT_LEFT, TEXT_RIGHT)
    bases = {y: row_background(image, y, window) for y in range(top, bottom + 1)}
    left = right = None
    for x in range(lo, hi):
        if any(is_ink(image, x, y, bases[y]) for y in range(top, bottom + 1)):
            if left is None:
                left = x
            right = x
    if left is None:
        raise ValueError(f"no ink in band {band} window {window}")
    return left, min(right + 3, hi)


def band_colours(image: itp.ItpImage, band, window=None) -> dict[str, tuple]:
    """The ink colours this line is drawn with, split body / red / blue."""
    top, bottom = band
    lo, hi = window or (TEXT_LEFT, TEXT_RIGHT)
    counts: dict[tuple, int] = {}
    bases = []
    for y in range(top, bottom + 1):
        base = row_background(image, y, window)
        bases.append(base)
        for x in range(lo, hi):
            colour = image.palette[image.pixels[y * image.width + x]]
            if colour[3] > 200 and abs(lum(colour) - base) > 70:
                counts[colour] = counts.get(colour, 0) + 1
    if not counts:
        raise ValueError(f"no ink colour in band {band}")
    page = sum(bases) / len(bases)

    def redness(colour):
        return colour[0] - (colour[1] + colour[2]) / 2

    def blueness(colour):
        return colour[2] - (colour[0] + colour[1]) / 2

    # Not the commonest ink: at this size most of a glyph is antialiasing, so
    # the commonest colour is a pale halfway tone and the line came out washed
    # out.  The stroke core is the ink that is furthest from the page.
    common = max(counts.values())
    solid = [c for c in counts if counts[c] >= common * 0.2] or list(counts)
    body = max(solid, key=lambda c: abs(lum(c) - page))
    strong = [c for c in counts if counts[c] >= 3] or list(counts)
    red = max(strong, key=redness)
    blue = max(strong, key=blueness)
    return {
        "body": body,
        "red": red if redness(red) > 25 else body,
        "blue": blue if blueness(blue) > 25 else body,
    }


def anchors(canvas: Image.Image, band, left: int, right: int, pad: int, busy,
            reference: float):
    """The clean rows just above and below a band, skipping rules and neighbours.

    Three things must stay out of the ramp.  A band widened to fit taller Hangul
    can run into the next line, so rows another line occupies are skipped.  A
    table cell is fenced by a dark rule one row outside it, and a ramp anchored
    on the rule paints the cell the colour of its own border.  And a row that
    still carries a little ink is worse than it looks: the ramp samples every
    column separately, so one surviving stroke becomes a stripe running the
    height of the repair.

    So a candidate is judged on how much of it is ink -- how many columns sit
    far from ``reference``, the band's own background measured before anything
    was cleared.  A clean row scores zero, a row with a stroke or two scores a
    little, and a rule scores one because all of it is far from the cell.  The
    cleanest rows win.  A side with nothing but rules and ink left returns
    ``None`` and the caller mirrors the other side or fills flat.
    """
    top, bottom = band
    columns = list(range(left, right)) or [left]
    pixels = canvas.load()

    def roughness(y: int) -> float:
        """How much of the row is stroke edges.

        This is what tells a row that still has type on it from a row of
        illustration.  Both can be far from flat, but text is thin strokes with
        a hard edge on either side, so most of a text row is transitions, while
        a picture -- even a busy one -- shades.  Anchoring on a row of type is
        what turns a repair into vertical stripes, because the ramp samples
        every column on its own and drags each stroke down the whole band.
        """
        edges = sum(
            1 for a, b in zip(columns, columns[1:])
            if abs(lum(pixels[a, y]) - lum(pixels[b, y])) > 40
        )
        return edges / max(1, len(columns) - 1)

    def belongs(y: int) -> bool:
        """Is this row the same background as the band, or something else?

        Rejects a table rule, which is one flat colour and not the cell's, and
        the row of a neighbouring band -- the phase banner under a name cell,
        the next section's tint -- whose colour would be dragged into the repair.
        """
        values = [lum(pixels[x, y]) for x in columns]
        return abs(statistics.median(values) - reference) <= 35

    def side(candidates):
        rows = [y for y in candidates
                if 0 <= y < canvas.height and y not in busy and belongs(y)]
        if not rows:
            return None
        rows.sort(key=lambda y: (round(roughness(y), 2), abs(y - top)))
        # Giving up means a flat fill, and that is only ever the right answer
        # for a table cell.  Across a caption laid over an illustration a flat
        # block is far worse than a ramp sampled from slightly textured rows,
        # so only a narrow band is allowed to bail out.
        if roughness(rows[0]) > 0.22 and right - left <= 200:
            return None
        keep = rows[:pad]
        while len(keep) < pad:
            keep.append(keep[-1])
        return keep

    return side(range(top - 1, top - 9, -1)), side(range(bottom + 1, bottom + 9))


def band_plate(image: itp.ItpImage, band, left: int, right: int):
    """The colour behind a line, as ``(colour, brightness)``.

    Two wrong answers had to be ruled out.  The median of each row is the
    background only while the background is most of the row, and a table cell
    packed with a long name is not: on the record pages that median came out
    the brown of the text outline and the repair painted the cell brown.  The
    commonest exact colour is worse still on a page of parchment -- the
    parchment is textured, so its tone is spread over a dozen near-identical
    values while the glyph cores are all one exact colour, and the mode picks
    the ink.

    So: take the median brightness of the whole band, which is the background
    as long as the glyphs cover less than half of it, and then the commonest
    exact colour that sits at that brightness.  Texture and ink both lose.
    """
    values, colours = [], []
    for y in range(band[0], band[1] + 1):
        row = y * image.width
        for x in range(left, right):
            colour = image.palette[image.pixels[row + x]]
            colours.append(colour)
            values.append(lum(colour))
    if not values:
        return None, 128.0
    base = statistics.median(values)
    counts: dict[tuple, int] = {}
    for colour in colours:
        if abs(lum(colour) - base) <= 25:
            counts[colour] = counts.get(colour, 0) + 1
    if not counts:
        return None, base
    return max(counts, key=lambda c: counts[c]), base


def erase(canvas: Image.Image, band, left: int, right: int, reference: float,
          snap: int = 4, pad: int = 3, flat: bool = False, busy=frozenset(),
          plate=None) -> None:
    """Repaint one line, column by column, as a ramp across the cleared band.

    ``pad`` is how many clean rows above and below are averaged for the two
    ends of the ramp.  ``flat`` fills with the mean of both ends instead, which
    is what a flat cell wants.
    """
    top, bottom = band
    pixels = canvas.load()
    top = max(top, pad + 1)
    bottom = min(bottom, canvas.height - pad - 2)
    above, below = anchors(canvas, (top, bottom), left, right, pad, busy, reference)
    if above is None and below is None:
        # Rules on both sides: no row to sample, so repaint the cell with its
        # own colour, read from under the glyphs before anything was cleared.
        pixels_flat = plate or (255, 255, 255, 255)
        for x in range(left, right):
            for y in range(top, bottom + 1):
                pixels[x, y] = pixels_flat
        return
    # When one side had nothing usable it is mirrored, and a ramp between two
    # copies of the same rows is just a flat fill.
    above, below = above or below, below or above
    span = max(1, below[-1] - above[-1])
    for x in range(left, right):
        start = [sum(pixels[x, y][c] for y in above) / len(above) for c in range(4)]
        end = [sum(pixels[x, y][c] for y in below) / len(below) for c in range(4)]
        if flat:
            start = end = [(start[c] + end[c]) / 2 for c in range(4)]
        for y in range(top, bottom + 1):
            t = (y - above[-1]) / span
            pixels[x, y] = tuple(
                min(255, round((start[c] + (end[c] - start[c]) * t) / snap) * snap)
                for c in range(4)
            )


def nearest(palette, colour, cache: dict) -> int:
    hit = cache.get(colour)
    if hit is not None:
        return hit
    best, score = 0, None
    for index, entry in enumerate(palette):
        if entry[3] < 128:
            continue
        d = sum((entry[c] - colour[c]) ** 2 for c in range(3))
        if score is None or d < score:
            best, score = index, d
    cache[colour] = best
    return best


def line_box(spans, font) -> tuple[int, int, int, int]:
    """Where the ink of a whole line sits relative to a draw origin of (0, 0)."""
    text = "".join(t for _key, t in spans) or " "
    probe = Image.new("L", (int(font.getlength(text)) + 16, 40), 0)
    ImageDraw.Draw(probe).text((4, 8), text, font=font, fill=255)
    box = probe.getbbox() or (4, 8, 4, 8)
    return (box[0] - 4, box[1] - 8, box[2] - 4, box[3] - 8)


def draw_spans(canvas: Image.Image, spans, origin, colours, font) -> int:
    """Draw one line span by span; returns the column the line ends at.

    ``origin`` is where the ink starts, not where the glyph box starts: the
    line is measured first and shifted so its ink lands on the rows the
    Japanese occupied.  Getting this wrong clips the top off every glyph,
    which is what the first render did.
    """
    x, y = origin
    for _key, text in spans:
        for source, target in SUBSTITUTE.items():
            text = text.replace(source, target)
    for key, text in spans:
        for source, target in SUBSTITUTE.items():
            text = text.replace(source, target)
        colour = colours.get(key, colours["body"])
        mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(mask).text((x, y), text, font=font, fill=255)
        # These pages are revision 1004, a raw 8bpp plane, so unlike the quiz
        # atlases there is no 16-colour block limit to quantise for: the glyph
        # keeps its full antialiasing, which is what makes 12px Hangul legible.
        mask = mask.point(lambda v: min(255, int(v * 1.25)))
        canvas.paste(Image.new("RGBA", canvas.size, colour), (0, 0), mask)
        x += int(round(font.getlength(text)))
    return x


def apply(image: itp.ItpImage, lines, snap: int = 4) -> Image.Image:
    """Erase the Japanese and draw the Korean; returns the canvas for preview.

    ``lines`` is a list of dicts::

        {"y": (top, bottom), "text": [(colour key, string), ...],
         "bold": False, "x": (left, right), "pad": 3, "flat": False,
         "size": 12, "align": "left" | "center" | "right"}

    Only ``y`` and ``text`` are required; ``x`` restricts the window a line is
    measured, cleared and drawn in, which is what keeps a table column or the
    page counter out of its neighbour.
    """
    canvas = to_image(image)
    plan = []
    for line in lines:
        band = tuple(line["y"])
        window = tuple(line["x"]) if line.get("x") else None
        left, right = ink_span(image, band, window)
        # The colour the ramp has to land on, measured before anything is
        # cleared.  Both the anchor test and the flat fallback use it, so they
        # cannot disagree about what the background of this line even is.
        plate, reference = band_plate(image, band, left, right)
        plan.append({
            "band": band, "left": left, "right": right, "line": line,
            "colours": band_colours(image, band, window),
            "plate": plate, "reference": reference,
        })

    fonts: dict[tuple[bool, int], ImageFont.FreeTypeFont] = {}

    def font_for(bold: bool, size: int):
        key = (bold, size)
        if key not in fonts:
            fonts[key] = ImageFont.truetype(str(FONT_BOLD if bold else FONT_PATH), size)
        return fonts[key]

    # Lay every line out before anything is cleared: a line whose Korean is
    # taller than the rows the Japanese used has to widen the band it clears,
    # or the glyph tops are simply not written back into the atlas.
    for step in plan:
        line, band = step["line"], step["band"]
        size = line.get("size", FONT_SIZE)
        while True:
            font = font_for(line.get("bold", False), size)
            box = line_box(line["text"], font)
            if box[3] - box[1] <= band[1] - band[0] + 3 or size <= 9:
                break
            size -= 1
        step["font"] = font
        step["box"] = box
        # One row of margin each side: the coverage boost lights up a faint row
        # above the nominal ink top, and a band that does not include it leaves
        # the top pixel row of the Japanese behind as a hairline streak.
        height = box[3] - box[1]
        step["rows"] = (max(1, band[0] - 1),
                        min(image.height - 2, max(band[1], band[0] + height - 1) + 1))
        width = int(round(sum(font.getlength(text) for _key, text in line["text"])))
        x = step["left"]
        if line.get("align") == "right":
            x = max(step["left"], step["right"] - width - 2)
        elif line.get("align") == "center":
            lo, hi = tuple(line["x"]) if line.get("x") else (step["left"], step["right"])
            x = lo + max(0, (hi - lo - width) // 2)
        # The repair has to reach wherever the line is actually drawn, or a
        # centred label loses the columns left of the Japanese it replaces.
        step["x"] = x
        step["left"] = min(step["left"], x)

    busy = {y for step in plan for y in range(step["rows"][0], step["rows"][1] + 1)}
    for step in plan:
        line = step["line"]
        erase(canvas, step["rows"], step["left"], step["right"], step["reference"],
              snap=snap, pad=line.get("pad", 3), flat=line.get("flat", False), busy=busy,
              plate=step["plate"])

    for step in plan:
        line, band, box, font = step["line"], step["band"], step["box"], step["font"]
        end = draw_spans(canvas, line["text"], (step["x"] - box[0], band[0] - box[1]),
                         step["colours"], font)
        step["limit"] = max(step["right"], min(end + 2, TEXT_RIGHT))

    data = list(canvas.getdata())
    pixels = list(image.pixels)
    cache: dict = {}
    for step in plan:
        top, bottom = step["rows"]
        for y in range(top, bottom + 1):
            for x in range(step["left"], step["limit"]):
                offset = y * image.width + x
                pixels[offset] = nearest(image.palette, data[offset], cache)
    image.pixels = pixels
    image.revision = 1004
    return canvas
