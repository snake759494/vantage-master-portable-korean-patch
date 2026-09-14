# -*- coding: utf-8 -*-
"""Draw the Korean gallery text into ``data/system/galle*.itp``.

The gallery pages are 512x512 revision-1004 atlases with the Japanese baked in:
a katakana name and five description lines over the character art.  The text is
NOT drawn from the executable -- the executable happens to carry the same
sentences for the thirty masters, which is where their Korean comes from, but
the twenty-four Netiaal pages exist only as pixels and were read off the atlas.

Which page is who comes from a table in BOOT.BIN at 0x178BAE: 54 records of
0x2A bytes, the Japanese name at +0 and the texture stem at +0x1A.

Clearing the Japanese is the hard part, because the panel behind it is not flat
-- the character art shows through.  Every page puts its text on exactly the
same rows, with three clean rows between each pair, so a line is erased by
interpolating each column between the clean row above and the clean row below.
The panel shades vertically and slowly, so the repair does not show; filling
with a flat colour does, which is why it is not done that way.
"""

from __future__ import annotations

import io
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw, ImageFont

import falcom_itp as itp

ISO_DIR = "/PSP_GAME/USRDIR/data/system"
BOOT_PATH = "/PSP_GAME/SYSDIR/BOOT.BIN"
TABLE_AT = 0x178BAE
TABLE_STRIDE = 0x2A
TABLE_TEXTURE = 0x1A

TEXT_LEFT = 128
# The Japanese never reaches past here; beyond it the character art starts and
# the button box sits at 400, so this is where the repair has to stop.
TEXT_RIGHT = 352
# The katakana never passes 250; the element badge beside it starts at 290.
NAME_RIGHT = 250

# Measured on the atlases, and identical on all 54: five description rows on a
# 16-pixel pitch with the katakana name above them.
NAME_BAND = (171, 182)
BODY_BANDS = [(187, 197), (203, 213), (219, 229), (235, 245), (251, 261)]

FONT_PATH = Path("NanumSquareNeo-cBd.ttf")
FONT_SIZE = 12
# Rows a Hangul line reaches above the band the Japanese used.  A syllable
# stacks its vowel over its consonant, so twelve-pixel Hangul is twelve or
# thirteen rows deep where the kanji it replaces was eleven.
ASCENT = 2


MIDDLE_DOT = {"・": "·"}


def cstring(data: bytes, at: int) -> str:
    return data[at : data.find(b"\0", at)].decode("cp932")


def gallery_table(boot: bytes) -> list[tuple[str, str]]:
    """[(texture stem, Japanese name)] in the order the gallery menu lists them."""
    rows: list[tuple[str, str]] = []
    at = TABLE_AT
    while True:
        name, texture = cstring(boot, at), cstring(boot, at + TABLE_TEXTURE)
        if not texture.startswith("galle"):
            return rows
        rows.append((texture, name))
        at += TABLE_STRIDE


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


def near_white(image: itp.ItpImage, x: int, y: int) -> bool:
    """A glyph core: the baked text is white, the art beside it is not."""
    colour = image.palette[image.pixels[y * image.width + x]]
    return colour[3] > 128 and min(colour[:3]) > 205 and max(colour[:3]) - min(colour[:3]) < 25


def band_offset(image: itp.ItpImage) -> int:
    """How far this page sits from the reference rows.

    The five description lines are always on a 16-pixel pitch, but a page may
    put them a pixel higher or lower -- and a single row of kanji left behind is
    exactly the ghosting that showed up first.  Taking the first bright row is
    not enough: on a page whose art is pale, the background itself reads as
    bright and the probe lands four rows early, which misaligns every band and
    leaves most of the Japanese in place.  So every candidate is scored on how
    well it separates the text rows from the three clean rows above each of
    them, and the best separation wins.
    """
    rows = {
        y: sum(1 for x in range(TEXT_LEFT, TEXT_RIGHT) if near_white(image, x, y))
        for y in range(BODY_BANDS[0][0] - 6, BODY_BANDS[-1][1] + 7)
    }

    def score(shift: int) -> int:
        ink = gaps = 0
        for top, bottom in BODY_BANDS:
            ink += sum(rows.get(y + shift, 0) for y in range(top, bottom + 1))
            gaps += sum(rows.get(y + shift, 0) for y in range(top - 3, top))
        return ink - 3 * gaps

    return max(range(-3, 4), key=score)


def lit(image: itp.ItpImage, x: int, y: int) -> bool:
    colour = image.palette[image.pixels[y * image.width + x]]
    return colour[3] > 128 and min(colour[:3]) > 150


def ink_right(image: itp.ItpImage, band: tuple[int, int], limit: int) -> int:
    """The last column the baked text reaches, so the art past it is left alone."""
    last = TEXT_LEFT
    for x in range(TEXT_LEFT, limit):
        if any(near_white(image, x, y) for y in range(band[0], band[1] + 1)):
            last = x
    return min(last + 4, limit)


def erase(canvas: Image.Image, band: tuple[int, int], left: int, right: int,
          flat: bool = False, snap: int = 4) -> None:
    """Repaint one line of text, column by column.

    The Japanese is dense enough that the background under it is simply gone --
    at 11 pixels a kanji fills most of its band -- so it cannot be recovered,
    only replaced.  Each column is redrawn as a ramp between the clean rows
    above and below, each end being the mean of three rows so noise in a single
    row cannot streak down the band.  ``right`` stops at the last column the
    Japanese reached, so the art beside a short line is left untouched.

    ``flat`` and ``snap`` are the fallback when the rebuilt atlas will not fit
    the byte budget it has to be spliced back into: a flat column and a coarser
    palette make longer horizontal runs, which is what the ED7 stream packs.
    """
    top, bottom = band
    pixels = canvas.load()
    span = (bottom + 3) - (top - 3)
    for x in range(left, right):
        start = [sum(pixels[x, top - 1 - k][c] for k in range(3)) / 3 for c in range(4)]
        end = [sum(pixels[x, bottom + 1 + k][c] for k in range(3)) / 3 for c in range(4)]
        if flat:
            start = end = [(start[c] + end[c]) / 2 for c in range(4)]
        for y in range(top, bottom + 1):
            t = (y - (top - 3)) / span
            pixels[x, y] = tuple(
                min(255, round((start[c] + (end[c] - start[c]) * t) / snap) * snap)
                for c in range(4)
            )


def ink_colour(image: itp.ItpImage, band: tuple[int, int], right: int):
    """The commonest bright ink in a band; the name line is tinted per element."""
    counts: dict[tuple[int, int, int, int], int] = {}
    for y in range(band[0], band[1] + 1):
        for x in range(TEXT_LEFT, right):
            colour = image.palette[image.pixels[y * image.width + x]]
            if colour[3] > 200 and min(colour[:3]) > 150:
                counts[colour] = counts.get(colour, 0) + 1
    if not counts:
        return (255, 255, 255, 255)
    common = [colour for colour, count in counts.items() if count >= 4] or list(counts)
    return max(common, key=lambda colour: sum(colour[:3]))


def nearest(palette, colour, cache: dict):
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


def apply(image: itp.ItpImage, name: str, lines: list[str],
          flat: bool = False, snap: int = 4) -> Image.Image:
    """Erase the Japanese and draw the Korean; returns the canvas for preview."""
    if len(lines) > len(BODY_BANDS):
        raise ValueError(f"{len(lines)} lines will not fit {len(BODY_BANDS)} rows")
    canvas = to_image(image)
    shift = band_offset(image)
    name_band = (NAME_BAND[0] + shift, NAME_BAND[1] + shift)
    body_bands = [(top + shift, bottom + shift) for top, bottom in BODY_BANDS]
    name_right = NAME_RIGHT
    name_colour = ink_colour(image, name_band, name_right)
    body_colour = ink_colour(image, body_bands[0], TEXT_RIGHT)

    limits = {name_band: ink_right(image, name_band, name_right)}
    for band in body_bands:
        limits[band] = ink_right(image, band, TEXT_RIGHT)
    for band, right in limits.items():
        erase(canvas, band, TEXT_LEFT, right, flat, snap)

    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    draw = ImageDraw.Draw(canvas)
    # Every pixel the lettering covers, so the copy back into the atlas is not
    # confined to the rows the Japanese used.  A kanji fills eleven rows; the
    # same sentence in Hangul is twelve or thirteen, because a syllable stacks
    # a vowel over a consonant, and writing back only the old rows sliced the
    # top off every line in the gallery.
    written = Image.new("L", canvas.size, 0)
    for text, band, colour in [(name, name_band, name_colour)] + [
        (line, band, body_colour) for line, band in zip(lines, body_bands)
    ]:
        if not text:
            continue
        for source, target in MIDDLE_DOT.items():
            text = text.replace(source, target)
        box = draw.textbbox((0, 0), text, font=font)
        origin = (TEXT_LEFT, band[1] - box[3])
        # Hangul at 12px antialiases to a grey core, which reads much dimmer
        # than the crisp Japanese it replaces; boosting coverage puts the
        # stroke centres back at full ink and keeps the edges soft.
        mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(mask).text(origin, text, font=font, fill=255)
        # Quantise the coverage: a smooth alpha ramp lands on dozens of
        # palette entries and the atlas stops fitting the byte budget it has to
        # be spliced back into.  Three levels keep the glyph soft enough.
        boosted = mask.point(lambda v: min(255, int(v * 1.7)))
        mask = boosted.point(lambda v: 0 if v < 60 else (140 if v < 170 else 255))
        canvas.paste(Image.new("RGBA", canvas.size, colour), (0, 0), mask)
        written.paste(mask, (0, 0), mask)
        limits[band] = max(limits[band], min(TEXT_LEFT + box[2] + 2, TEXT_RIGHT))

    data = list(canvas.getdata())
    cover = list(written.getdata())
    pixels = list(image.pixels)
    cache: dict = {}
    for band in [name_band] + body_bands:
        right = limits[band]
        # The rows the Japanese occupied, which have been repainted, plus
        # wherever the Korean reaches above them.  Above the band the canvas is
        # background the erase never touched, so only the pixels the lettering
        # actually covers are taken -- copying the whole row back would requantise
        # art that was already right.
        for y in range(band[0] - ASCENT, band[1] + 1):
            if y < 0:
                continue
            for x in range(TEXT_LEFT, right):
                offset = y * image.width + x
                if y < band[0] and not cover[offset]:
                    continue
                pixels[offset] = nearest(image.palette, data[offset], cache)
    image.pixels = pixels
    image.revision = 1004
    return canvas
